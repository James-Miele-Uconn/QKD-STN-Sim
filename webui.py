import gradio as gr # type: ignore
import os
from time import sleep
from modules.ui_customization import *
from modules.ui_main_options import *
from modules.run_sim import *

# Global variables
need_restart = False


# Update global variable checking for reload
def update_reload():
    global need_restart
    need_restart = True


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
    graphs = get_graph_lists()
    random_graphs = graphs["random_graphs"]
    chain_graphs = graphs["chain_graphs"]
    specific_graphs = graphs["specific_graphs"]

    # Layout for the UI
    with gr.Blocks(title="QKD Simulator", theme=theme, css=css) as app:
        # Align both left and right together
        with gr.Row():
            # Settings
            with gr.Column(scale=1):
                # Simulation control values
                with gr.Group():
                    with gr.Row(equal_height=True):
                        # General toggleable options
                        with gr.Column():
                            using_stn = gr.Checkbox(
                                label="Use STNs",
                                info="Use STNs as intermediate nodes if checked, otherwise use TNs",
                                value=False
                            )
                            simple = gr.Checkbox(
                                label="Simple Simulator",
                                info="Run the simple simulator",
                                value=False,
                                visible=False
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

                # Graph settings
                with gr.Group():
                    with gr.Row():
                        graph_type = gr.Dropdown(
                            ["Chain", "Specific", "Random"],
                            value="Chain",
                            label="Graph Type",
                            interactive=True
                        )
                        graph = gr.Dropdown(
                            chain_graphs,
                            value=chain_graphs[0],
                            label="Graph"
                        )
                        num_users = gr.Number(
                            value=2,
                            label="Number of User Pairs",
                            interactive=True
                        )
                    saved_graph = gr.File(
                        label="Upload Graph File",
                        height=120
                    )

                # Other settings
                with gr.Row():
                    round_time = gr.Number(
                        value=-1,
                        label="Round time",
                        info="Time (in ms) per simulator round\nUse -1 for min of quantum or classical time"
                    )
                    classic_time = gr.Number(
                        value=-1,
                        label="Classical time",
                        info="Time (in ms) for classical phase\nUse -1 for optimized value"
                    )

                # Cost equation values
                with gr.Row():
                    N = gr.Number(
                        value=10000000,
                        label="N",
                        info="Rounds in quantum phase"
                    )
                    Q = gr.Number(
                        value=0.02,
                        label="Q",
                        info="Link-level noise in the system",
                        step=None
                    )
                    px = gr.Number(
                        value=0.2,
                        label="px",
                        info="Probability of choosing X basis in quantum phase",
                        step=None
                    )

                # Batch processing controls
                with gr.Accordion(label="Batch Options", open=False):
                    with gr.Row():
                        batch_x_type = gr.Dropdown(
                            ["None", "round_time", "classic_time", "N", "Q", "px"],
                            value="None",
                            show_label=False
                        )
                        batch_x_val = gr.Textbox(
                            show_label=False,
                            placeholder="Enter a comma-separated list of values"
                        )

                    with gr.Row():
                        batch_y_type = gr.Dropdown(
                            ["None", "round_time", "classic_time", "N", "Q", "px"],
                            value="None",
                            show_label=False
                        )
                        batch_y_val = gr.Textbox(
                            show_label=False,
                            placeholder="Enter a comma-separated list of values"
                        )

                    with gr.Row():
                        batch_z_type = gr.Dropdown(
                            ["None", "round_time", "classic_time", "N", "Q", "px"],
                            value="None",
                            show_label=False
                        )
                        batch_z_val = gr.Textbox(
                            show_label=False,
                            placeholder="Enter a comma-separated list of values"
                        )

            # Simulation control and results
            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column():
                        cur_graph = gr.Image(
                            image_mode=None,
                            type="filepath",
                            label="Graph",
                            show_download_button=False,
                            interactive=False
                        )
                        with gr.Row():
                            purge_graphs = gr.Button(
                                value="Purge Graph Images",
                                variant="stop"
                            )

                    with gr.Column():
                        with gr.Row():
                            start_sim = gr.Button(
                                value="Run Simulation",
                                variant="primary",
                                size="lg"
                            )
                            purge_results = gr.Button(
                                value="Purge Results",
                                variant="stop"
                            )
                        results = gr.Markdown(
                            value="<center><h1>Results will be shown here.</h1></center>",
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

        # Handle simulation setup options
        sim_limits.change(update_sim_limits, inputs=[sim_limits], outputs=[sim_time, sim_keys, limit_msg, start_sim])
        graph_type.change(update_graph_options, inputs=[graph_type], outputs=[graph])

        # Handle main simulation options
        start_sim.click(run_sim, inputs=[N, Q, px, sim_time, sim_keys, using_stn, simple, graph_type, graph, num_users, saved_graph, round_time, classic_time, batch_x_type, batch_x_val, batch_y_type, batch_y_val, batch_z_type, batch_z_val], outputs=[results, cur_graph])
        purge_results.click(purge_result_csvs)
        purge_graphs.click(purge_graph_images, outputs=[cur_graph])

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