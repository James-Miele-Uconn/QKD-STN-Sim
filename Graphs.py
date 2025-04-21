from Assets import *


def get_graph_dict(cur_graph):
    """Get dictionary of dictionaries for desired graph.

    Args:
      cur_graph: Which graph dictionary to use
    
    Returns:
      Dictionary of dictionaries for desired graph setup.
    """
    graph_dicts = {
        "0": {
            "a0": {"n0": {"weight": 1}},
            "b0": {"n1": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "n1": {"weight": 1}},
            "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}}
        },
        "1": {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n0": {"weight": 1}},
            "b1": {"n0": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        },
        "2": {
            "a0": {"n0": {"weight": 1}},
            "a1": {"n0": {"weight": 1}},
            "b0": {"n1": {"weight": 1}},
            "b1": {"n1": {"weight": 1}},
            "n0": {"a0": {"weight": 1}, "a1": {"weight": 1}, "n1": {"weight": 1}},
            "n1": {"n0": {"weight": 1}, "b0": {"weight": 1}, "b1": {"weight": 1}}
        }
    }

    return graph_dicts[cur_graph]


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