import gradio as gr # type: ignore
import os
from shutil import rmtree
from .Graphs import get_graph_lists

# Function to update which simulation termination options are available
def update_sim_limits(limit_vals):
    if "Time" in limit_vals:
        new_time = gr.Number(value=10000000, visible=True)
    else:
        new_time = gr.Number(value=-1, visible=False)
    
    if "Keys" in limit_vals:
        new_keys = gr.Number(value=1000000, visible=True)
    else:
        new_keys = gr.Number(value=-1, visible=False)

    if not limit_vals:
        new_msg = gr.Label(visible=True)
        new_start = gr.Button(interactive=False)
    else:
        new_msg = gr.Label(visible=False)
        new_start = gr.Button(interactive=True)

    return [new_time, new_keys, new_msg, new_start]


# Update grpah options
def update_graph_options(graph_type):
    graphs = get_graph_lists()
    random_graphs = graphs["random_graphs"]
    chain_graphs = graphs["chain_graphs"]
    specific_graphs = graphs["specific_graphs"]

    if graph_type == "Chain":
        new_graph_opts = gr.Dropdown(chain_graphs, value=chain_graphs[0])
    elif graph_type == "Specific":
        new_graph_opts = gr.Dropdown(specific_graphs, value=specific_graphs[0])
    else:
        new_graph_opts = gr.Dropdown(random_graphs, value=random_graphs[0])
    
    return new_graph_opts


# Purge graph images
def purge_graph_images():
    if os.path.exists("./graphs"):
        try:
            rmtree("./graphs")
        except Exception as e:
            raise gr.Error(e)

    gr.Info("Graph images removed")    
    return gr.Image(value=None)


# Purge result csv files
def purge_result_csvs():
    if os.path.exists("./results"):
        try:
            rmtree("./results")
        except Exception as e:
            raise gr.Error(e)
    
    gr.Info("Result CSV files removed")