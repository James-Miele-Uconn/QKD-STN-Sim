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
from numpy import log10, log2, log, ceil
from time import time
from Assets import *


def find_available_src_nodes(graph, nodes):
    """Find any source nodes in a graph which do not currently have a task.

    Args:
      graph: The graph to check nodes in.
      nodes: Container of nodes to check.

    Returns:
      List of source nodes not currently involved in a task.
    """
    available_nodes = list()

    for node in nodes:
        if not graph.has_node(node):
            continue

        if graph.nodes[node]["data"].operation is None:
            available_nodes.append(node)
    
    for node in available_nodes:
        nodes.append(nodes.pop(nodes.index(node)))
    
    return available_nodes


def determine_new_keys(nodes):
    """Determine which source nodes will attempt to generate keys this simulator round.

    Args:
      nodes: Container of node objects to iterate over.
    
    Returns:
      List of nodes attempting key generation this simulator round.
    """
    new_keys = list()

    for node in nodes:
        new_keys.append(node)
    
    return new_keys


def determine_routes(graph, nodes):
    """Determine optimal routes to allow as many new QKD instances as possible.

    Args:
      graph: Graph to look for paths in.
      nodes: List of nodes which want to start QKD.

    Returns:
      List of paths to use for new QKD instances.
    """
    best_paths = list()
    used_nodes = set()

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


def continue_QKD(node_mode, current_qkd, info, N, classic_time):
    """Simulate QKD for each given QKD instance.

    Args:
      node_mode: Whether the non-user nodes are TNs or STNs
      current_qkd: List of QKD_Inst objects to handle this simulator round.
      info: Info_Tracker object for tracking stats.
      N: Number of rounds of communication within the quantum phase of QKD
      classic_time: Amount of time (in ms) for the classical phase of QKD.
    
    Returns:
      Tuple containing time spent (in ms) in this simulator round, along with a list of nodes to add back into running graph.
    """
    add_back = list()
    photon_gen_rate = 10**9 / 1000                      # Pulse rate in miliseconds
    valid_rate = 0.1                                    # Probability of valid photon generation
    cur_quantum_times = [0.0 for qkd in current_qkd]    # List of time taken for quantum phase of qkd in this simulator round
    cur_round_time = 0                                  # Time (in ms) taken this simulator round, based on maximum time for a qkd instance to perform quantum phase

    # Handle quantum phase of qkd
    for i in range(len(current_qkd)):
        qkd = current_qkd[i]
        # Start timers for new QKD instances
        if qkd.operation is None:
            qkd.switch_operation()
        
        # Find time required for each qkd instance in quantum phase
        if qkd.operation == "Quantum":
            cur_time = N / photon_gen_rate
            cur_quantum_times[i] = cur_time
            qkd.switch_operation(timer_val=classic_time)

    # Find time spent for quantum phase for this round. If no quantum phase, then default to average time needed (in ms) to send N qubits
    cur_round_time = max(cur_quantum_times)
    if cur_round_time == 0:
        cur_round_time = N / photon_gen_rate
    
    # Handle classic phase of qkd based on time spent on quantum phase of this simulator round
    for i in range(len(current_qkd)):
        qkd = current_qkd[i]
        if qkd.operation == "Classic":
            cur_timer = qkd.dec_timer(cur_round_time - cur_quantum_times[i])
            if cur_timer == 0:
                qkd.switch_operation()

    # Release any nodes that are no longer needed
    for qkd in current_qkd:
        # Determine actions based on current operation
        if qkd.operation is None:
            # Track relevant statistics at QKD completion
            info.increase_all(qkd.p, node_mode)

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

    return (cur_round_time, add_back)


def parse_arguments():
    """Parse command-line arguments using argparse.

    Returns:
      All arguments that can be set through the cli.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-D", help="\tprint debug messages.", action="store_true")
    parser.add_argument("--sim_time", metavar="", help="\tamount of time (in sec) that should be simulated in this run. Defaults to 100 sec.", default=100000, type=float)
    parser.add_argument("--quantum_rounds", metavar="", help="\tnumber of rounds of communication within the quantum phase of QKD. Defaults to 10^7 rounds.", default=10**7, type=int)
    parser.add_argument("--classic_time", metavar="", help="\tamount of time (in ms) for the classical phase of QKD. Defaults to 100 ms.", default=100, type=float)
    parser.add_argument("--node_mode", metavar="", help="\twhether non-use nodes should be TNs or STNs. Defaults to TN.", default="TN", type=str)
    parser.add_argument("--link_noise", metavar="", help="\tlink-level noise in the system, as a decimal representation of a percentage. Defaults to 0.02.", default=0.02, type=float)
    parser.add_argument("--prob_x_basis", metavar="", help="\tprobability that the X basis is chosen in the quantum phase of QKD. Defaults to 0.2.", default=0.2, type=float)
    args = parser.parse_args()

    return args


def main(graph, nodes, graph_dict, info, node_mode, sim_time, N, Q, px, classic_time, debug, src_nodes=None):
    """Entry point for the program.
    
    Args:
      graph: NetworkX Graph of network.
      nodes: Dict of node names and their respective Node objects
      graph_dict: Dict of node names with their neighbors (and any edge attributes)
      info: Info_Tracker object for tracking various statistics for this run of the simulator.
      node_mode: Whether the non-user nodes are TNs or STNs.
      sim_time: Amount of time (in sec) that should be simulated in this run.
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
    total_sim_time = 0.0    # Total amount of time (in sec) that has passed in this simulation
    rounds = 0  # Total number of rounds that have passe din this simulation

    # Get time simulation actually starts running for debug messages
    if debug:
        start_time = time()
        last_time = 0

    # Run simulation
    while total_sim_time < sim_time:
        # Step 1: Find all nodes which will attempt to start QKD this simulator round
        available_nodes = find_available_src_nodes(RG, node_schedule)
        new_keys = determine_new_keys(available_nodes)
        
        # Step 2: Find all routes to use for starting new QKD instances
        new_routes = determine_routes(RG, new_keys)
        route_nodes = remove_and_store_new_QKD(RG, new_routes)

        # Step 3: Handle newly started QKD instances
        for route in route_nodes:
            active_qkd.append(QKD_Inst(route))

        # Step 4: For all current QKD instances, continue operation
        cur_round_time, to_add = continue_QKD(node_mode, active_qkd, info, N, classic_time)

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
        total_sim_time += (cur_round_time / 1000)
        rounds += 1
        if debug:
            cur_time = time() - start_time
            if ((cur_time - last_time) > 15):
                print(f"[{cur_time//60:.0f}m {cur_time%60:.1f}s] {rounds:,} rounds finished.")
                last_time = cur_time
    
    print(f"\nNon-user nodes: {node_mode}s\n\nSimulator rounds: {rounds - 1:,}\nRounds per quantum phase: 10^{log10(N):.0f}\nLink-level noise: {Q * 100:.1f}%\nX-basis probability: {px}")
    print(f"\nEfficiency Statistics:\nKeys generated: {info.finished_keys:,}\nAverage key rate: {info.average_key_rate:.4f}\nCost incurred: {info.total_cost:,.0f}\n")


# Run the simulator if this file is called
if __name__ == "__main__":
    # Get parameters from cli
    args = parse_arguments()

    # Define variables to be used in math
    N = args.quantum_rounds
    Q = args.link_noise
    px = args.prob_x_basis

    # Create Info_Tracker object and get information required for setup
    info = Info_Tracker(N, Q, px)

    # Determine test graph to use
    cur_graph = 2

    # Mapping of node names to neighbor names (and edge attributes)
    if cur_graph == 1:
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

    # Mapping of node names to Node objects
    if cur_graph == 1:
        test_nodes = {"a0": User(name="a0"),
                "a1": User(name="a1"),
                "b0": User(name="b0"),
                "b1": User(name="b1")}
        if args.node_mode == "TN":
            test_nodes["n0"] = TN(name="n0")
        elif args.node_mode == "STN":
            test_nodes["n0"] = STN(name="n0", neighbors=test_graph_dict["n0"].keys(), J=info.J)
    elif cur_graph == 2:
        test_nodes = {"a0": User(name="a0"),
                "a1": User(name="a1"),
                "b0": User(name="b0"),
                "b1": User(name="b1")}
        if args.node_mode == "TN":
            test_nodes["n0"] = TN(name="n0")
            test_nodes["n1"] = TN(name="n1")
        elif args.node_mode == "STN":
            test_nodes["n0"] = STN(name="n0", neighbors=test_graph_dict["n0"].keys(), J=info.J)
            test_nodes["n1"] = STN(name="n1", neighbors=test_graph_dict["n1"].keys(), J=info.J)
    
    # Set graph based on desired test graph setup
    graph_dict = test_graph_dict
    nodes = test_nodes

    # Record of which nodes are allowed to start QKD
    source_nodes = ["a0", "a1"]

    # Make graph
    G = Graph(graph_dict)
    set_node_attributes(G, nodes, "data")

    # Start simulator
    main(G, nodes, graph_dict, info, args.node_mode, args.sim_time, args.quantum_rounds, args.link_noise, args.prob_x_basis, args.classic_time, args.D, src_nodes=source_nodes)