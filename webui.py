import gradio as gr # type: ignore
import os
from time import sleep
from Main import *

# Global variables
need_restart = False


# Javascript needed for changing theme mode
def theme_mode_js():
    return """
    () => {
        document.body.classList.toggle('dark');
    }
    """


# Update theme color
def update_theme_color(cur_color):
    if not os.path.exists("./customization"):
        try:
            os.mkdir("./customization")
        except:
            pass

    with open("./customization/theme_color.txt", "w", encoding="utf-8") as outf:
        outf.write(cur_color)


# Update global variable checking for reload
def update_reload():
    global need_restart
    need_restart = True


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


# Run simulation
def run_sim(N, Q, px, sim_time, sim_keys, using_stn, simple, graph, round_time, classic_time):
    """Run simulation with given variables.

    Args:
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      sim_time: Amount of time to simulate, ignored if -1. Will stop early if sim_keys enabled and finishes sooner.
      sim_time: Amount of keys to simulate, ignored if -1. Will stop early if sim_time enabled and finishes sooner.
      using_stn: Whether the simulator is using STNs.
      simple: Whether to run the simple simulator. Defaults to False.
      graph: Network graph to use.
      round_time: Amount of time (in ms) per sim round.
      classic_time: Amount of time (in ms) for the classical phase of QKD.

    Returns:
      Image of graph used and formatted information about simulation run.
    """
    results = start_sim(N, Q, px, sim_time, sim_keys, using_stn, simple, graph, round_time, classic_time)
    graph_image_name = results["graph_image_name"]

    sim_output = "\n[]-----[ Simulation Information ]-----[]"
    sim_output += f"\nNon-user nodes: {results['node_mode']}s"
    sim_output += f"\n\nTime simulated: {results['total_sim_time'] / 1000:,.2f} sec"
    sim_output += f"\nSimulator rounds: {results['rounds']:,}"
    sim_output += f"\nRounds per quantum phase: {N:.0f}"
    sim_output += f"\nLink-level noise: {Q * 100:.1f}%"
    sim_output += f"\nX-basis probability: {px}"
    sim_output += f"\n\n[]-----[ Efficiency Statistics ]-----[]"
    sim_output += f"\nTotal keys generated: {results['finished_keys']:,}"
    sim_output += f"\nKeys by user pair:"
    for user in results['user_pair_keys'].keys():
        sim_output += f"\n----[ {user}-b{user[1]} ]: {results['user_pair_keys'][user]:,}"
    sim_output += f"\nAverage key rate: {results['average_key_rate']:.4f}"
    sim_output += f"\nCost incurred: {results['total_cost']:,.0f}"

    return [gr.Markdown(value=sim_output), gr.Image(value=f"./graphs/{graph}/{graph_image_name}")]



# Get customization options, to allow storing/reloading UI theme
def get_setup_vars():
    """Create variables to pass to UI Block object.

    Returns:
      CSS, color option, and theme object to give to UI Block object.
    """
    # Add custom css
    css = """
    footer {visibility: hidden}
    """

    # Get currently set theme color
    saved_color = "rose"
    try:
        if not os.path.exists("./customization"):
            try:
                os.mkdir("./customization")
            except:
                pass
        with open("./customization/theme_color.txt", "r") as inf:
            saved_color = inf.readline().strip()
    except:
        pass

    # Specify theme to use
    theme =  gr.themes.Default(
        primary_hue=saved_color,
        secondary_hue=saved_color
    ).set(
        color_accent_soft='*primary_700',
        color_accent_soft_dark='*primary_700',
        border_color_primary='*primary_800',
        border_color_primary_dark='*primary_800',
        border_color_accent='*primary_950',
        border_color_accent_dark='*primary_950'
    )

    return (css, saved_color, theme)


# Layout for the UI
def setup_layout(css, saved_color, theme):
    """Create Block object to be used for UI.

    Args:
      css: String with custom CSS.
      saved_color: String naming the saved color.
      theme: Customized Default theme.
    
    Returns:
      The Block object to be used for the UI.
    """
    # Layout for the UI
    with gr.Blocks(title="QKD Simulator", theme=theme, css=css) as app:
        # Align both left and right together
        with gr.Row():
            # Settings
            with gr.Column(scale=2):
                # Simulation control values
                with gr.Group():
                    with gr.Row(equal_height=True):
                        # General toggleable options
                        with gr.Column():
                            using_stn = gr.Checkbox(
                                label="Use STNs",
                                info="Use STNs as intermediat nodes if checked, otherwise use TNs",
                                value=False
                            )
                            simple = gr.Checkbox(
                                label="Simple Simulator",
                                info="Run the simple simulator",
                                value=False
                            )

                        # Control for which options are shown
                        with gr.Column():
                            sim_limits = gr.CheckboxGroup(
                                ["Time", "Keys"],
                                value=["Time"],
                                label="Simulation Termination Values",
                                info="Which values to use to determine when to terminate simulation"
                            )

                        # Edit the currently selected options
                        with gr.Column():
                            with gr.Row():
                                sim_time = gr.Number(
                                    value=10000000,
                                    label="Simulate Time",
                                    info="Seconds to simulate"
                                )
                                sim_keys = gr.Number(
                                    value=-1,
                                    label="Simulate Keys",
                                    info="Keys to simulate",
                                    visible=False
                                )
                            limit_msg = gr.Label(
                                value="At least one option must be selected.",
                                show_label=False,
                                visible=False
                            )

                # Other settings
                with gr.Row():
                    graph = gr.Radio(
                        [0, 1, 2],
                        value=2,
                        label="Graph",
                        info="Which network graph to use",
                        interactive=True
                    )
                    round_time = gr.Number(
                        value=-1,
                        label="Round time",
                        info="Miliseconds per simulator round, use -1 for classic time"
                    )
                    classic_time = gr.Number(
                        value=-1,
                        label="Classical time",
                        info="Miliseconds for classical phase, use -1 for optimized value"
                    )

                # Cost equation values
                with gr.Row():
                    N = gr.Number(
                        value=10000000,
                        label="N",
                        info="Number of rounds in quantum phase"
                    )
                    Q = gr.Number(
                        value=0.02,
                        label="Q",
                        info="Link-level noise in the system"
                    )
                    px = gr.Number(
                        value=0.2,
                        label="px",
                        info="Probability of choosing X basis in quantum phase"
                    )

            # Simulation control and results
            with gr.Column(scale=1):
                start_sim = gr.Button(
                    value="Run Simulation",
                    variant="primary",
                    size="lg"
                )
                cur_graph = gr.Image(
                    image_mode=None,
                    type="filepath",
                    label="Graph",
                    show_download_button=False,
                    placeholder="Graph image will appear here",
                    interactive=False
                )
                results = gr.Markdown(
                    value="Results will be shown here.",
                    line_breaks=True,
                    container=True,
                    min_height=100
                )
        
        # Customization options
        with gr.Sidebar(width=200, open=False, position="right"):
            # Settings that don't need a restart
            with gr.Column():
                theme_mode = gr.Button(
                    value="Toggle Dark Mode",
                    variant="primary"
                )

            # Settings that do need a restart            
            with gr.Group():
                gr.Markdown("Require restart:")
                theme_color = gr.Dropdown(
                    ["slate", "gray", "zinc", "neutral", "stone", "red", "orange", "amber", "yellow", "lime", "green", "emerald", "teal", "cyan", "sky", "blue", "indigo", "violet", "purple", "fuchsia", "pink", "rose"],
                    value=saved_color,
                    label="Theme Color",
                    interactive=True
                )
                reload_app = gr.Button(
                    value="Reload UI\n(Requires refreshing tab)",
                    variant="stop"
                )

        # Handle main simulation options
        sim_limits.change(update_sim_limits, inputs=[sim_limits], outputs=[sim_time, sim_keys, limit_msg, start_sim])
        start_sim.click(run_sim, inputs=[N, Q, px, sim_time, sim_keys, using_stn, simple, graph, round_time, classic_time], outputs=[results, cur_graph])

        # Handle customization options
        mode_js = theme_mode_js()
        theme_mode.click(None, js=mode_js)
        theme_color.change(update_theme_color, inputs=[theme_color])
        reload_app.click(update_reload)

    return app


if __name__ == "__main__":
    while True:
        # Launch UI with customization settings
        css, saved_color, theme = get_setup_vars()
        app = setup_layout(css, saved_color, theme)
        app.launch(
            favicon_path="./customization/favicon.png",
            share=False,
            server_name="0.0.0.0",
            server_port=7861,
            prevent_thread_lock=True
        )

        # Loop until restart requested
        while not need_restart:
            sleep(0.5)

        # Handle restart
        need_restart = False
        app.close()