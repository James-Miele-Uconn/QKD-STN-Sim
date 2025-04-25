from Assets import *


random_graphs = [
    "Grid"
]
chain_graphs = [
    "1 Node",
    "2 Nodes",
    "3 Nodes",
    "4 Nodes"
]
specific_graphs = [
    "Single Node, Two User Pairs",
    "Dumbell, Two Nodes, Two User Pairs"
]


def get_graph_dict(graph_type, cur_graph, num_users):
    """Get dictionary of dictionaries for desired graph.

    Args:
      graph_type: What type of graph to use.
      cur_graph: Which graph dictionary to use
      num_users: How many user pairs are in the graph
    
    Returns:
      Dictionary of dictionaries for desired graph setup.
    """
    specific_graph_dicts = {
        "Single Node, Two User Pairs": {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n0": {"weight": 1}},
            "b1": {"n0": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        },
        "Dumbell, Two Nodes, Two User Pairs": {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n1": {"weight": 1}},
            "b1": {"n1": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "n1": {"weight": 1}},
            "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        }
    }

    if graph_type == "Specific":
        graph_dict = specific_graph_dicts[cur_graph]
    elif graph_type == "Chain":
        graph_dict = dict()
        num_inner = int(cur_graph.split(" ")[0])
        first_inner_dict = dict()
        last_inner_dict = dict()
        
        for i in range(num_users):
            graph_dict[f"a{i}"] = {"n0": {"weight": 1}}
            first_inner_dict[f"a{i}"] = {"weight": 1}
            graph_dict[f"b{i}"] = {f"n{num_inner-1}": {"weight": 1}}
            last_inner_dict[f"b{i}"] = {"weight": 1}

        for i in range(1, num_inner-1):
            graph_dict[f"n{i}"] = {f"n{i-1}": {"weight": 1}, f"n{i+1}": {"weight": 1}}

        if num_inner == 1:
            first_inner_dict.update(last_inner_dict)
            graph_dict["n0"] = first_inner_dict
        else:
            first_inner_dict["n1"] = {"weight": 1}
            last_inner_dict[f"n{num_inner-2}"] = {"weight": 1}
            graph_dict["n0"] = first_inner_dict
            graph_dict[f"n{num_inner-1}"] = last_inner_dict
    else:
        graph_dict = None

    return graph_dict


def get_graph_nodes(graph_dict, J=None):
    """Get dictionary of nodes to use for given graph.

    Args:
      graph_dict: Dictionary of dictionaries containing information on current graph layout.
      J: Keys allowed by STN before running TN functionality. Defaults to None.
    
    Returns:
      Dictionary containing node objects to be used for the current graph.
    """
    graph_nodes = dict()
    for node in graph_dict.keys():
        if node[0] == "n":
            if J is None:
                graph_nodes[node] = TN(name=node)
            else:
                graph_nodes[node] = STN(name=node, neighbors=graph_dict[node].keys(), J=J)
        else:
            graph_nodes[node] = User(name=node)

    return graph_nodes