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


def continue_QKD(current_qkd, N):
    """Simulate QKD for each given QKD instance.

    Args:
      current_qkd: List of QKD_Inst objects to handle this simulator round.
      N: Number of rounds in the quantum phase of QKD
    
    Returns:
      List of nodes to add back into running graph.
    """
    add_back = list()

    for qkd in current_qkd:
        # Get current operation
        cur_op = qkd.operation

        # Start timers for new QKD instances
        if cur_op is None:
            qkd.switch_operation(N)
        
        # Modify timer based on amount of time that passes per simulator round
        cur_timer = qkd.dec_timer(N)

        # Check if operation should be changed
        if cur_timer == 0:
            cur_op = qkd.switch_operation(N)
        
        # Determine actions based on current operation
        if cur_op is None:
            # Release any nodes left in this QKD instance
            for node in qkd.route:
                # Flip node out of TN mode
                if node.node_type == "STN":
                    node.TN_mode = False

                # Release node from QKD instance
                add_back.append(node)
                qkd.route.remove(node)
        elif cur_op == "Classic":
            # Decrement STN J for each neighbor, releasing STN if all neighbors have J above 0
            to_remove = list()
            for node in qkd.route:
                if node.node_type == "STN":
                    # If not currently refreshing secret key pool, decrease secret key pool
                    if not node.TN_mode:
                        # Use secret key pool bits
                        left_n = qkd.route[qkd.route.index(node) - 1]
                        right_n = qkd.route[qkd.route.index(node) + 1]
                        left_j = node.use_pool_bits(left_n.name, N)
                        right_j = node.use_pool_bits(right_n.name, N)

                        # Refresh secret key bits and flip to TN mode, as needed
                        should_flip = False
                        if (left_j == 0):
                            node.refresh_pool_bits(left_n.name, N)
                            should_flip = True
                        if (right_j == 0):
                            node.refresh_pool_bits(right_n.name, N)
                            should_flip = True
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
    parser.add_argument("--rounds", default=100, type=int)
    parser.add_argument("-N", "--timestep", default=10**4, type=int)
    parser.add_argument("-M", "--node_mode", default="TN", type=str)
    args = parser.parse_args()

    return args


def main(graph, nodes, graph_dict, rounds, N, src_nodes=None):
    """Entry point for the program.
    
    Args:
      graph: NetworkX Graph of network.
      nodes: Dict of node names and their respective Node objects
      graph_dict: Dict of node names with their neighbors (and any edge attributes)
      rounds: Number of rounds the simulator should run for.
      N: Length of time for the quantum phase of QKD.
      src_nodes: What nodes are allowed to start the key generation process. Defaults to None.
    """
    # Define parameters
    RG = graph.copy()   # Copy graph to make running graph for use during simulation
    node_schedule = deepcopy(src_nodes)    # Copy of src_nodes, to be modified during simulation
    active_qkd = list() # List of actively running QKD instances
    finished_keys = 0   # Total keys generated by the simulation

    # Run simulation
    for sim_round in range(rounds):
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
        to_add = continue_QKD(active_qkd, N)

        # Step 5: Remove any finished QKD instances
        for qkd in active_qkd:
            if qkd.is_finished():
                active_qkd.remove(qkd)
                finished_keys += 1
        
        # Step 6: Add any freed nodes back into the running graph
        for node in to_add:
            name = node.name
            RG.add_node(name, data=node)
            for neighbor in graph_dict[name]:
                if RG.has_node(neighbor):
                    RG.add_edge(name, neighbor)
    
    print(f"Simulator rounds: {rounds}\nTime per simulator round: {N}")
    print(f"Keys generated: {finished_keys}")


# Run the simulator if this file is called
if __name__ == "__main__":
    # Get parameters from cli
    args = parse_arguments()

    # Mapping of node names to neighbor names (and edge attributes)
    graph_dict = {
        "a0": {"n0": {"weight": 1}},
        "a1": {"n0": {"weight": 1}},
        "b0": {"n1": {"weight": 1}},
        "b1": {"n1": {"weight": 1}},
        "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "n1": {"weight": 1}},
        "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
    }

    # Mapping of node names to Node objects
    nodes = {"a0": User(name="a0"),
             "a1": User(name="a1"),
             "b0": User(name="b0"),
             "b1": User(name="b1")}
    if args.node_mode == "TN":
        nodes["n0"] = TN(name="n0")
        nodes["n1"] = TN(name="n1")
    elif args.node_mode == "STN":
        nodes["n0"] = STN(name="n0", neighbors=graph_dict["n0"].keys())
        nodes["n1"] = STN(name="n1", neighbors=graph_dict["n1"].keys())

    # Record of which nodes are allowed to start QKD
    source_nodes = ["a0", "a1"]

    # Make graph
    G = Graph(graph_dict)
    set_node_attributes(G, nodes, "data")


    # Start simulator
    main(G, nodes, graph_dict, args.rounds, args.timestep, src_nodes=source_nodes)