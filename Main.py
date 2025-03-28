"""
A simulator to measure efficiency of STN networks compared to TN networks.
Multiple cost models will be used for analysis.

To show graph: draw(G), plt.show() ### Must be done in cmd, else it won't work
"""

from networkx import Graph, set_node_attributes, has_path, all_shortest_paths, draw
from copy import deepcopy
import matplotlib.pyplot as plt
import random as rand
import argparse
from numpy import round, log10, log2, log, ceil
from time import time
from sys import exit
from Assets import *
from Simple import * # type: ignore


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


def continue_QKD(using_stn, current_qkd, info, quantum_time, classic_time, round_time):
    """Simulate QKD for each given QKD instance.

    Args:
      using_stn: Whether the non-user nodes are STNs.
      current_qkd: List of QKD_Inst objects to handle this simulator round.
      info: Info_Tracker object for tracking stats.
      quantum_time: Amount of time (in ms) for generating the qubits in the quantum phase of QKD.
      classic_time: Amount of time (in ms) for the classical phase of QKD.
      round_time: Amount of time (in ms) that is simulated every round.
    
    Returns:
      List of nodes to add back into running graph.
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
    parser.add_argument("--graph", metavar="", help="\twhich graph to use. Defaults to 2 for graph 2.", default=2, type=int)
    parser.add_argument("--sim_time", metavar="", help="\tamount of time (in sec) that should be simulated in this run. Defaults to 100000000 sec.", default=10000000, type=float)
    parser.add_argument("--round_time", metavar="", help="\tamount of time (in ms) per sim round. Defaults to -1, to match max of quantum or classic time.", default=-1, type=float)
    parser.add_argument("--classic_time", metavar="", help="\tamount of time (in ms) for the classical phase of QKD. Defaults to -1, for matching quantum time.", default=-1, type=float)
    parser.add_argument("--N", metavar="", help="\tnumber of rounds of communication within the quantum phase of QKD. Defaults to 10^7 rounds.", default=10**7, type=int)
    parser.add_argument("--Q", metavar="", help="\tlink-level noise in the system, as a decimal representation of a percentage. Defaults to 0.02.", default=0.02, type=float)
    parser.add_argument("--px", metavar="", help="\tprobability that the X basis is chosen in the quantum phase of QKD. Defaults to 0.2.", default=0.2, type=float)
    args = parser.parse_args()

    return args


def main(graph, nodes, graph_dict, info, using_stn, sim_time, round_time, N, Q, px, classic_time, debug, src_nodes=None):
    """Entry point for the program.
    
    Args:
      graph: NetworkX Graph of network.
      nodes: Dict of node names and their respective Node objects
      graph_dict: Dict of node names with their neighbors (and any edge attributes)
      info: Info_Tracker object for tracking various statistics for this run of the simulator.
      using_stn: Whether the simulator is using STNs.
      sim_time: Amount of time (in sec) that should be simulated in this run.
      round_time: Amount of time (in ms) per sim round.
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      classic_time: Amount of time (in ms) for the classical phase of QKD.
      debug: Whether or not debug messages should be printed.
      src_nodes: What nodes are allowed to start the key generation process. Defaults to None.
    """
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
            # Ensure valid time
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
            to_add = continue_QKD(using_stn, active_qkd, info, qubit_rate, classic_time, round_time)

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
    
    sim_output = ""
    if using_stn:
        node_mode = "STN"
    else:
        node_mode = "TN"
    sim_output += f"\n[]-----[ Simulation Information ]-----[]\nNon-user nodes: {node_mode}s\n\nTime simulated: {total_sim_time / 1000:,.2f} sec\nSimulator rounds: {rounds:,}\nRounds per quantum phase: 10^{log10(N):.0f}\nLink-level noise: {Q * 100:.1f}%\nX-basis probability: {px}\n"
    sim_output += f"\n[]-----[ Efficiency Statistics ]-----[]\nTotal keys generated: {info.finished_keys:,}\nKeys by user pair:\n"
    for user in info.user_pair_keys.keys():
        sim_output += f"    {user}-b{user[1]}: {info.user_pair_keys[user]:,}\n"
    sim_output += f"Average key rate: {info.average_key_rate:.4f}\nCost incurred: {info.total_cost:,.0f}\n"

    print(sim_output)

# Run the simulator if this file is called
if __name__ == "__main__":
    # Get parameters from cli
    args = parse_arguments()

    # Define variables to be used in math
    N = args.N
    Q = args.Q
    px = args.px

    # Determine test graph to use
    cur_graph = args.graph

    # Mapping of node names to neighbor names (and edge attributes)
    if cur_graph == 0:
        test_graph_dict = {
            "a0": {"n0": {"weight": 1}},
            "b0": {"n1": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "n1": {"weight": 1}},
            "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}}
        }
    elif cur_graph == 1:
        test_graph_dict = {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n0": {"weight": 1}},
            "b1": {"n0": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        }
    elif cur_graph == 2:
        test_graph_dict = {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n1": {"weight": 1}},
            "b1": {"n1": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "n1": {"weight": 1}},
            "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        }

    # Record of which nodes are allowed to start QKD
    source_nodes = [node for node in test_graph_dict.keys() if node.startswith('a')]

    # Create Info_Tracker object and get information required for setup
    info = Info_Tracker(source_nodes, N, Q, px)

    # Mapping of node names to Node objects
    if cur_graph == 0:
        test_nodes = {"a0": User(name="a0"),
                "b0": User(name="b0")}
        if args.stn:
            test_nodes["n0"] = STN(name="n0", neighbors=test_graph_dict["n0"].keys(), J=info.J)
            test_nodes["n1"] = STN(name="n1", neighbors=test_graph_dict["n1"].keys(), J=info.J)
        else:
            test_nodes["n0"] = TN(name="n0")
            test_nodes["n1"] = TN(name="n1")
    elif cur_graph == 1:
        test_nodes = {"a0": User(name="a0"),
                "a1": User(name="a1"),
                "b0": User(name="b0"),
                "b1": User(name="b1")}
        if args.stn:
            test_nodes["n0"] = STN(name="n0", neighbors=test_graph_dict["n0"].keys(), J=info.J)
        else:
            test_nodes["n0"] = TN(name="n0")
    elif cur_graph == 2:
        test_nodes = {"a0": User(name="a0"),
                "a1": User(name="a1"),
                "b0": User(name="b0"),
                "b1": User(name="b1")}
        if args.stn:
            test_nodes["n0"] = STN(name="n0", neighbors=test_graph_dict["n0"].keys(), J=info.J)
            test_nodes["n1"] = STN(name="n1", neighbors=test_graph_dict["n1"].keys(), J=info.J)
        else:
            test_nodes["n0"] = TN(name="n0")
            test_nodes["n1"] = TN(name="n1")
    
    # Set graph based on desired test graph setup
    graph_dict = test_graph_dict
    nodes = test_nodes

    # Make graph
    G = Graph(graph_dict)
    set_node_attributes(G, nodes, "data")

    if args.simple:
        # Run simple simulation, then exit
        simple_sim(G, N, Q, px, args.sim_time, args.stn) # type: ignore
        exit()
    else:
        # Start simulator
        main(G, nodes, graph_dict, info, args.stn, args.sim_time, args.round_time, N, Q, px, args.classic_time, args.D, src_nodes=source_nodes)