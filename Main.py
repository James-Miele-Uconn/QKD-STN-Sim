"""
A simulator to measure efficiency of STN networks compared to TN networks.
Multiple cost models will be used for analysis.

To show graph: draw(G), plt.show() ### Must be done in cmd, else it won't work
"""

from networkx import Graph, set_node_attributes, has_path, all_shortest_paths, kamada_kawai_layout, draw_networkx_edges, draw_networkx_nodes, draw_networkx_labels # type: ignore
from copy import deepcopy
import matplotlib.pyplot as plt
import random as rand
import argparse, os
from numpy import round, log10, log2, log, ceil
from time import time, strftime, gmtime
from sys import exit
from Assets import *
from Simple import * # type: ignore
from Graphs import * # type: ignore


def get_vars(cur_time, N, Q, px, sim_time, sim_keys, using_stn, graph_type, graph, num_users, round_time, classic_time):
    """Setup variables to be used for simulation.

    Args:
      cur_time: Time as of the start of the simulator.
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      sim_time: Amount of time to simulate, ignored if -1. Will stop early if sim_keys enabled and finishes sooner.
      sim_time: Amount of keys to simulate, ignored if -1. Will stop early if sim_time enabled and finishes sooner.
      using_stn: Whether the simulator is using STNs.
      graph_type: What type of graph to use.
      graph: Network graph to use.
      num_users: Number of user nodes in the network.
      round_time: Amount of time (in ms) per sim round.
      classic_time: Amount of time (in ms) for the classical phase of QKD.

    Returns:
      Dictionary of needed variables.
    """
    # Get parameters from cli
    args = parse_arguments()

    # Ensure some terminating variable is set
    if (args.sim_time == -1) and (args.sim_keys == -1):
        print("\nError:\nBoth sim_time and sim_keys are disabled, but at least one needs to be enabled to run.")
        exit(1)

    # Set variables passed by UI
    if N is not None:
        args.N = N
    if Q is not None:
        args.Q = Q
    if px is not None:
        args.px = px
    if sim_time is not None:
        args.sim_time = sim_time
    if sim_keys is not None:
        args.sim_keys = sim_keys
    if using_stn is not None:
        args.stn = using_stn
    if graph is not None:
        args.graph = graph
    if round_time is not None:
        args.round_time = round_time
    if classic_time is not None:
        args.classic_time = classic_time

    # Determine test graph to use
    cur_graph = args.graph

    # Get graph dict
    graph_dict = get_graph_dict(graph_type, cur_graph, num_users)

    # Record of which nodes are allowed to start QKD
    source_nodes = [node for node in graph_dict.keys() if node.startswith('a')]

    # Create Info_Tracker object and get information required for setup
    info = Info_Tracker(source_nodes, args.N, args.Q, args.px)

    # Get graph nodes
    if using_stn:
        graph_nodes = get_graph_nodes(graph_dict, info.J)
    else:
        graph_nodes = get_graph_nodes(graph_dict)

    # Make graph
    G = Graph(graph_dict)
    set_node_attributes(G, graph_nodes, "data")

    # Save figure for current graph
    fname = f"Graph_{cur_graph}_{cur_time}.png"
    if not os.path.exists("./graphs"):
        try:
            os.mkdir("./graphs")
        except:
            pass
    if not os.path.exists(f"./graphs/{cur_graph}"):
        try:
            os.mkdir(f"./graphs/{cur_graph}")
        except:
            pass
    pos = kamada_kawai_layout(G)
    user_nodes = source_nodes + [f"b{node[1]}" for node in source_nodes]
    inner_nodes = [node for node in graph_nodes.keys() if node not in user_nodes]
    labels = dict()
    for node in graph_nodes.keys():
        labels[node] = node
    draw_networkx_nodes(G, pos, nodelist=user_nodes, node_color="tab:red")
    draw_networkx_nodes(G, pos, nodelist=inner_nodes, node_color="tab:blue")
    draw_networkx_edges(G, pos)
    draw_networkx_labels(G, pos, labels)
    plt.tight_layout()
    plt.axis("off")
    plt.savefig(f"./graphs/{cur_graph}/{fname}")

    output = {
        "cur_time": cur_time,
        "args": args,
        "G": G,
        "graph_nodes": graph_nodes,
        "graph_dict": graph_dict,
        "info": info,
        "src_nodes": source_nodes,
        "graph_image_name": fname
    }

    return output


def find_available_src_nodes(graph, nodes):
    """Find any source nodes in a graph which do not currently have a task.

    Args:
      graph: The graph to check nodes in.
      nodes: Container of nodes to check.

    Returns:
      List of source nodes not currently involved in a task.
    """
    available_nodes = list()    # List for tracking nodes available to start QKD

    # Check if each node is in the running graph
    # If it is, check if it's currently being used for something (shouldn't happen but can't hurt to check)
    for node in nodes:
        if not graph.has_node(node):
            continue

        if graph.nodes[node]["data"].operation is None:
            available_nodes.append(node)
    
    return available_nodes


def determine_new_keys(nodes):
    """Determine which source nodes will attempt to generate keys this simulator round.

    Args:
      nodes: Container of node objects to iterate over.
    
    Returns:
      List of nodes attempting key generation this simulator round.
    """
    new_keys = list()   # List for tracking which available nodes will actually try to start QKD

    # For now this is deterministic, all nodes will make keys every round that they can
    for node in nodes:
        new_keys.append(node)
    
    return new_keys


def adjust_schedule(node_schedule, newest_active):
    """Given a schedule of when to serve which nodes, adjust the schedule based on the most recently used nodes.

    Args:
      node_schedule: List containing the desired order in which to serve users.
      newest_active: List containing the routes being used this round.
    
    Returns:
      List containing the new order in which to serve users.
    """
    new_schedule = node_schedule[:]     # Copy of old schedule, to be modified

    # Find source node for each route
    recently_served = [route[0] for route in newest_active]

    # Move each recently used source node to the end of the schedule
    for node in recently_served:
        new_schedule.append(new_schedule.pop(new_schedule.index(node)))
    
    return new_schedule


def determine_routes(graph, nodes):
    """Determine optimal routes to allow as many new QKD instances as possible.

    Args:
      graph: Graph to look for paths in.
      nodes: List of nodes which want to start QKD.

    Returns:
      List of paths to use for new QKD instances.
    """
    best_paths = list()     # List for tracking which routes will be used
    used_nodes = set()      # Set for ensuring chosen routes do not use overlapping nodes

    for node in nodes:
        # Find destination
        dest = f"b{node[1]}"

        # If no path to destination exists, skip node
        if not (graph.has_node(node) and graph.has_node(dest) and has_path(graph, node, dest)):
            continue

        # Find all shortest paths from source to dest in given graph
        paths = [p for p in all_shortest_paths(graph, source=node, target=dest)]

        # Find best path to use
        desired_path = paths[0]

        # Check if any node in path has already been slated for use
        path_viable = True
        for path_node in desired_path:
            if path_node in used_nodes:
                path_viable = False
                break
        
        # If path is available, add path to best_paths and nodes to used_nodes
        # Else, do nothing
        if path_viable:
            # Update schedule of nodes
            nodes.append(node)
            nodes.remove(node)

            # Lock in path as being used
            best_paths.append(desired_path)
            used_nodes.update(desired_path)
    
    return best_paths


def remove_and_store_new_QKD(graph, routes):
    """Remove nodes involved in new QKD instances from given graph.

    Args:
      graph: Graph to remove nodes from.
      routes: List of routes to be removed from graph.
    
    Returns:
      List of Node objects based on given routes.
    """
    route_nodes = list()    # List of lists of Node objects in each route

    for route in routes:
        cur_nodes = list()  # List to hold Node objects for each node in current route
        for node in route:
            cur_nodes.append(graph.nodes[node]["data"])     # Add Node object for current node
            graph.remove_node(node)
        route_nodes.append(cur_nodes)
    
    return route_nodes


def continue_QKD(using_stn, current_qkd, info, quantum_time, classic_time, round_time, sim_keys):
    """Simulate QKD for each given QKD instance.

    Args:
      using_stn: Whether the non-user nodes are STNs.
      current_qkd: List of QKD_Inst objects to handle this simulator round.
      info: Info_Tracker object for tracking stats.
      quantum_time: Amount of time (in ms) for generating the qubits in the quantum phase of QKD.
      classic_time: Amount of time (in ms) for the classical phase of QKD.
      round_time: Amount of time (in ms) that is simulated every round.
      sim_keys: Amount of keys to simulate in this run of the simulation.
    
    Returns:
      List of nodes to add back into running graph, or None if ending early due to sim_keys.
    """
    add_back = list()   # List to contain nodes which should be added back into the running graph
    leftover_time = [0 for qkd in current_qkd]  # List of time leftover after quantum phase, to allow work in classic phase

    # Continue QKD
    for i in range(len(current_qkd)):
        qkd = current_qkd[i]    # The current QKD_Inst object being considered
        left_quantum = False    # Whether or not the current qkd instance left the quantum phase this round

        # Start new QKD instances in quantum phase
        if qkd.operation is None:
            cur_quantum_time = quantum_time     # Time required for the quantum phase for this specific qkd instance
            qkd.switch_operation(timer_val=cur_quantum_time)
        
        # Handle quantum phase of qkd
        if qkd.operation == "Quantum":
            # If quantum phase will finish this round, note any time left in the round after quantum phase finishes
            if qkd.timer < round_time:
                leftover_time[i] = round_time - qkd.timer
            
            # Decrease time left by round time, switching operation if timer hits 0
            cur_timer = qkd.dec_timer(round_time)
            if cur_timer == 0:
                left_quantum = True
                qkd.switch_operation(timer_val=classic_time)


        # Hanlde classical phase of qkd
        if qkd.operation == "Classic":
            # Adjust time spent in classical phase by time left in round after quantum phase
            if not left_quantum:
                time_left = round_time
            else:
                time_left = leftover_time[i]
            
            # Decrease time left by time left (either time in round or time left from quantum phase), switching operation if timer hits 0
            cur_timer = qkd.dec_timer(time_left)
            if cur_timer == 0:
                qkd.switch_operation()

    # Release any nodes that are no longer needed
    for qkd in current_qkd:
        # Determine actions based on current operation
        if qkd.operation is None:
            # Track relevant statistics at QKD completion
            info.increase_all(qkd.route[0].name, qkd.p, using_stn)

            # Note which nodes are still left in QKD instace
            for node in qkd.route:
                # Flip node out of TN mode
                if node.node_type == "STN":
                    node.TN_mode = False

                # Add node to list of nodes to add back
                add_back.append(node)
            
            # Remove all nodes from this QKD instance's route. Probably not needed, but just in case.
            qkd.route = list()

            # Check if simulator should end when using sim_keys
            if sim_keys > -1:
                if info.finished_keys == sim_keys:
                    return None
        elif qkd.operation == "Classic":
            # Decrement STN J for each neighbor, releasing STN if all neighbors have J above 0
            to_remove = list()
            for node in qkd.route:
                if node.node_type == "STN":
                    # If not currently refreshing secret key pool, decrease secret key pool
                    if not node.TN_mode:
                        # Use secret key pool bits
                        left_n = qkd.route[qkd.route.index(node) - 1]
                        right_n = qkd.route[qkd.route.index(node) + 1]
                        left_j = node.use_pool_bits(left_n.name)
                        right_j = node.use_pool_bits(right_n.name)

                        # Refresh secret key bits and determine if node should flip to TN mode
                        should_flip = False
                        if (left_j == 0):
                            node.refresh_pool_bits(left_n.name, info.J)
                            should_flip = True
                        if (right_j == 0):
                            node.refresh_pool_bits(right_n.name, info.J)
                            should_flip = True

                        # Flip to TN mode if needed
                        if should_flip:
                            node.TN_mode = True
                            continue

                        # Mark node for removal
                        node.operation = None
                        to_remove.append(node)

            # Release STNs from QKD instance
            add_back += to_remove
            qkd.route = [n for n in qkd.route if (n not in to_remove)]

    return add_back


def parse_arguments():
    """Parse command-line arguments using argparse.

    Returns:
      All arguments that can be set through the cli.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-D", help="\tprint debug messages.", action="store_true")
    parser.add_argument("--stn", help="\tuse STNs instead of TNs.", action="store_true")
    parser.add_argument("--simple", help="\trun the simple simulator, then exit.", action="store_true")
    parser.add_argument("--graph", metavar="", help="\twhich graph to use. Defaults to Dumbell: Two Nodes, Two User Pairs.", default="Dumbell: Two Nodes, Two User Pairs", type=str)
    parser.add_argument("--sim_time", metavar="", help="\tamount of time (in sec) that should be simulated in this run, set to -1 to disable. Defaults to 100000000 sec.", default=10000000, type=float)
    parser.add_argument("--sim_keys", metavar="", help="\tnumber of keys that should be simulated in this run, set to -1 to disable. Defaults to -1.", default=-1, type=int)
    parser.add_argument("--round_time", metavar="", help="\tamount of time (in ms) per sim round. Defaults to -1, to match max of quantum or classic time.", default=-1, type=float)
    parser.add_argument("--classic_time", metavar="", help="\tamount of time (in ms) for the classical phase of QKD. Defaults to -1, for matching quantum time.", default=-1, type=float)
    parser.add_argument("--N", metavar="", help="\tnumber of rounds of communication within the quantum phase of QKD. Defaults to 10^7 rounds.", default=10**7, type=int)
    parser.add_argument("--Q", metavar="", help="\tlink-level noise in the system, as a decimal representation of a percentage. Defaults to 0.02.", default=0.02, type=float)
    parser.add_argument("--px", metavar="", help="\tprobability that the X basis is chosen in the quantum phase of QKD. Defaults to 0.2.", default=0.2, type=float)
    args = parser.parse_args()

    return args


def main_sim(vars):
    """Entry point for the program.
    
    Args:
      vars: Dictionary containing needed variables.
    
    Returns:
      Formatted string containing results of simulation.
    """
    # Get setup variables
    args = vars["args"]
    graph = vars["G"]   # NetworkX graph of network
    nodes = vars["graph_nodes"]   # Dict of node names and their respective Node objects
    graph_dict = vars["graph_dict"] # Dict of node names with their neighbors (and any edge attributes)
    info = vars["info"] # Info_Tracker object for tracking various statisitics for this run of the simulator
    src_nodes = vars["src_nodes"]   # What nodes are allowed to start the key generation process
    graph_image_name = vars["graph_image_name"]   # Name of graph image for current run

    # Get variables from argparse
    using_stn = args.stn    # Whether the simulator is using STNs
    sim_time = args.sim_time    # Amount of time to simulate, ignored if -1. Will stop early if sim_keys enabled and finishes sooner
    sim_keys = args.sim_keys    # Amount of keys to simulate, ignored if -1. Will stop early if sim_time enabled and finishes sooner
    round_time = args.round_time    # Amount of time (in ms) per sim round
    N = args.N  # Number of rounds of communication within the quantum phase of QKD
    Q = args.Q  # Link-level noise in the system, as a decimal representation of a percentage
    px = args.px    # Probability that the X basis is chosen in the quantum phase of QKD
    classic_time = args.classic_time    # Amount of time (in ms) for the classical phase of QKD
    debug = args.D  # Whether or not debug messages should be printed

    # Define parameters
    RG = graph.copy()   # Copy graph to make running graph for use during simulation
    node_schedule = deepcopy(src_nodes)    # Copy of src_nodes, to be modified during simulation
    active_qkd = list() # List of actively running QKD instances
    total_sim_time = 0.0    # Total amount of time (in ms) that has passed in this simulation
    rounds = 0  # Total number of rounds that have passed in this simulation

    # Find time required for qubit generation
    photon_gen_rate = 10**9 / 1000.0                    # Pulse rate in miliseconds
    valid_prob = 10**(-3)                               # Probability of valid photon generation
    valid_gen_rate = photon_gen_rate * valid_prob       # Rate of generation of valid qubits, based on pulse rate
    qubit_rate = N / valid_gen_rate                     # Time required to generate N valid qubits

    # Match classic time with quantum time, if desired
    # Based on ideal timing for all source nodes requiring the same STN
    if classic_time == -1:
        if len(src_nodes) == 1:
            classic_time = qubit_rate
        else:
            classic_time = qubit_rate * (len(src_nodes) - 1)

    # Match round time to max of quantim or classic time, if desired
    if round_time == -1:
        round_time = qubit_rate

    # Get time simulation actually starts running for debug messages
    if debug:
        start_time = time()
        last_time = 0

    # Run simulation
    try:
        while True:
            # Check for loop end and ensure valid time if using sim_time
            sim_time_left = float('inf')
            if sim_time > -1:
                sim_time_left = (sim_time * 1000) - total_sim_time
                if round(sim_time_left, decimals=2) <= 0:
                    break

            # Step 1: Find all nodes which will attempt to start QKD this simulator round
            available_nodes = find_available_src_nodes(RG, node_schedule)
            new_keys = determine_new_keys(available_nodes)        
            
            # Step 2: Find all routes to use for starting new QKD instances
            new_routes = determine_routes(RG, new_keys)
            route_nodes = remove_and_store_new_QKD(RG, new_routes)
            node_schedule = adjust_schedule(node_schedule, new_routes)

            # Step 3: Handle newly started QKD instances
            for route in route_nodes:
                active_qkd.append(QKD_Inst(route))

            # Step 4: For all current QKD instances, continue operation
            if sim_time_left < round_time:
                round_time = sim_time_left
            to_add = continue_QKD(using_stn, active_qkd, info, qubit_rate, classic_time, round_time, sim_keys)

            # Check for loop end if using sim_keys
            if to_add is None:
                break

            # Step 5: Remove any finished QKD instances
            for qkd in active_qkd:
                if qkd.is_finished():
                    active_qkd.remove(qkd)
            
            # Step 6: Add any freed nodes back into the running graph
            for node in to_add:
                name = node.name
                RG.add_node(name, data=node)
                for neighbor in graph_dict[name]:
                    if RG.has_node(neighbor):
                        RG.add_edge(name, neighbor)
            
            # Step 7: Track time passed in this simulator round
            total_sim_time += round_time
            rounds += 1
            if debug:
                cur_time = time() - start_time
                if ((cur_time - last_time) > 15):
                    print(f"[{cur_time//60:2.0f}m {cur_time%60:4.1f}s] {rounds:,} rounds finished, {total_sim_time / 1000:,.2f} sec passed.")
                    last_time = cur_time
    except:
        pass

    # Create information needed for output
    if using_stn:
        node_mode = "STN"
    else:
        node_mode = "TN"

    # Create output
    sim_output = {
        "cur_time": vars["cur_time"],
        "node_mode": node_mode,
        "total_sim_time": total_sim_time,
        "rounds": rounds,
        "finished_keys": info.finished_keys,
        "user_pair_keys": info.user_pair_keys,
        "average_key_rate": info.average_key_rate,
        "user_pair_key_rate": info.user_pair_key_rate,
        "total_cost": info.total_cost,
        "average_cost": info.average_cost,
        "user_pair_total_cost": info.user_pair_total_cost,
        "user_pair_average_cost": info.user_pair_average_cost,
        "graph_image_name": graph_image_name
    }

    return sim_output

def start_sim(N=None, Q=None, px=None, sim_time=None, sim_keys=None, using_stn=None, simple=False, graph_type=None, graph=None, num_users=None, round_time=None, classic_time=None):
    """Entry point for program.

    Args:
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      sim_time: Amount of time to simulate, ignored if -1. Will stop early if sim_keys enabled and finishes sooner.
      sim_time: Amount of keys to simulate, ignored if -1. Will stop early if sim_time enabled and finishes sooner.
      using_stn: Whether the simulator is using STNs.
      simple: Whether to run the simple simulator. Defaults to False.
      graph_type: What type of graph to use.
      graph: Network graph to use.
      num_users: Number of user nodes in the network.
      round_time: Amount of time (in ms) per sim round.
      classic_time: Amount of time (in ms) for the classical phase of QKD.

    Returns:
      Formatted string containing information about simulation run.
    """
    cur_time = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
    vars = get_vars(cur_time, N, Q, px, sim_time, sim_keys, using_stn, graph_type, graph, num_users, round_time, classic_time)
    if simple:
        # Run simple simulation
        return simple_sim(vars)
    else:
        # Start simulator
        return main_sim(vars)