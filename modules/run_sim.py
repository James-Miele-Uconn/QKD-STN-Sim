import gradio as gr # type: ignore
import os
from time import strftime, gmtime
from .Main import *

# Run simulation
def run_sim(N, Q, px, sim_time, sim_keys, using_stn, simple, graph_type, graph, num_users, saved_graph, round_time, classic_time, batch_x_type, batch_x_val, batch_y_type, batch_y_val, batch_z_type, batch_z_val):
    """Run simulation with given variables.

    Args:
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      sim_time: Amount of time to simulate, ignored if -1. Will stop early if sim_keys enabled and finishes sooner.
      sim_keys: Amount of keys to simulate, ignored if -1. Will stop early if sim_time enabled and finishes sooner.
      using_stn: Whether the simulator is using STNs.
      simple: Whether to run the simple simulator. Defaults to False.
      graph_type: What type of graph to use.
      graph: Network graph to use.
      num_users: Number of user nodes in the network.
      saved_graph: File containing information on desired graph to use.
      round_time: Amount of time (in ms) per sim round.
      classic_time: Amount of time (in ms) for the classical phase of QKD.
      batch_x_type: What variable to use for 'x' in batch processing.
      batch_x_val: What values to use for 'x' in batch processing.
      batch_y_type: What variable to use for 'y' in batch processing.
      batch_y_val: What values to use for 'y' in batch processing.
      batch_z_type: What variable to use for 'z' in batch processing.
      batch_z_val: What values to use for 'z' in batch processing.
      
    Returns:
      Image of graph used and formatted information about simulation run.
    """
    # Set up variables
    cur_time = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
    in_dict = {
        "N": N,
        "Q": Q,
        "px": px,
        "sim_time": sim_time,
        "sim_keys": sim_keys,
        "using_stn": using_stn,
        "simple": simple,
        "graph_type": graph_type,
        "graph": graph,
        "num_users": num_users,
        "round_time": round_time,
        "classic_time": classic_time,
        "cur_time": cur_time,
        "batch_x_type": batch_x_type,
        "batch_x_val": batch_x_val,
        "batch_y_type": batch_y_type,
        "batch_y_val": batch_y_val,
        "batch_z_type": batch_z_type,
        "batch_z_val": batch_z_val
    }

    saved_graph_dict = None
    if saved_graph is not None:
        try:
            with open(saved_graph, "r") as inf:
                saved_graph_dict = eval(inf.readline().strip())
        except Exception as e:
            raise gr.Error(e, duration=None)
    in_dict["saved_graph_dict"] = saved_graph_dict

    try:
        output = start_sim(in_dict)
    except Exception as e:
        raise gr.Error(e, duration=None)
    
    all_results = output["all_results"]
    graph_image_name = output["graph_image_name"]
    batch = output["batch"]

    # Save results to csv
    if not os.path.exists("./results"):
        try:
            os.mkdir("./results")
        except Exception as e:
            raise gr.Error(e, duration=None)
    try:
        first_res = all_results[0]
        with open(f"./results/results_{cur_time}.csv", "w", encoding="utf-8") as outf:
            # Write headers
            outf.write("Mode,Time_Simulated,Num_Rounds,N,Q,px,total_keys")
            for user in sorted(list(first_res['user_pair_keys'].keys())):
                outf.write(f",{user}-b{user[1:]}_keys")
            outf.write(",avg_key_rate")
            for user in sorted(list(first_res['user_pair_key_rate'].keys())):
                outf.write(f",{user}-b{user[1:]}_key_rate")
            outf.write(",total_cost")
            for user in sorted(list(first_res['user_pair_total_cost'].keys())):
                outf.write(f",{user}-b{user[1:]}_total_cost")
            outf.write(",avg_cost")
            for user in sorted(list(first_res['user_pair_average_cost'].keys())):
                outf.write(f",{user}-b{user[1:]}_avg_cost")
            
            # Write values
            for results in all_results:
                outf.write(f"\n{results['node_mode']},{results['total_sim_time']},{results['rounds']},{results['N']},{results['Q']},{results['px']},{results['finished_keys']}")
                for user in sorted(list(results['user_pair_keys'].keys())):
                    outf.write(f",{results['user_pair_keys'][user]}")
                outf.write(f",{results['average_key_rate']}")
                for user in sorted(list(results['user_pair_key_rate'].keys())):
                    outf.write(f",{results['user_pair_key_rate'][user]}")
                outf.write(f",{results['total_cost']}")
                for user in sorted(list(results['user_pair_total_cost'].keys())):
                    outf.write(f",{results['user_pair_total_cost'][user]}")
                outf.write(f",{results['average_cost']}")
                for user in sorted(list(results['user_pair_average_cost'].keys())):
                    outf.write(f",{results['user_pair_average_cost'][user]}")
    except Exception as e:
        raise gr.Error(e, duration=None)

    # Create formatted results to display
    if not batch:
        results = all_results[0]
        sim_output = "\n[]-----[ Simulation Information ]-----[]"
        sim_output += f"\nNon-user nodes: {results['node_mode']}s"
        sim_output += f"\n\nTime simulated: {results['total_sim_time'] / 1000:,.2f} sec"
        sim_output += f"\nSimulator rounds: {results['rounds']:,}"
        sim_output += f"\nRounds per quantum phase: {N:,.0f}"
        sim_output += f"\nLink-level noise: {Q * 100:.1f}%"
        sim_output += f"\nX-basis probability: {px}"
        sim_output += f"\n\n[]-----[ Efficiency Statistics ]-----[]"
        sim_output += f"\nTotal keys generated: {results['finished_keys']:,}"
        sim_output += f"\nKeys by user pair:"
        for user in sorted(list(results['user_pair_keys'].keys())):
            sim_output += f"\n----[ {user}-b{user[1:]} ]: {results['user_pair_keys'][user]:,}"
        sim_output += f"\n\nAverage key rate: {results['average_key_rate']:.4f}"
        sim_output += f"\nAverage key rate by user pair:"
        for user in sorted(list(results['user_pair_key_rate'].keys())):
            sim_output += f"\n----[ {user}-b{user[1:]} ]: {results['user_pair_key_rate'][user]:.4f}"
        sim_output += f"\n\nTotal cost incurred per secret key bit: {results['total_cost']:,.0f}"
        sim_output += f"\nTotal per-bit cost by user pair:"
        for user in sorted(list(results['user_pair_total_cost'].keys())):
            sim_output += f"\n----[ {user}-b{user[1:]} ]: {results['user_pair_total_cost'][user]:,.0f}"
        sim_output += f"\n\nAverage cost per secret key bit: {results['average_cost']:.2f}"
        sim_output += f"\nAverage per-bit cost by user pair:"
        for user in sorted(list(results['user_pair_average_cost'].keys())):
            sim_output += f"\n----[ {user}-b{user[1:]} ]: {results['user_pair_average_cost'][user]:.2f}"
    else:
        sim_output = "Batch results stored in csv file."

    return [gr.Markdown(value=sim_output), gr.Image(value=f"./graphs/{graph}/{graph_image_name}")]