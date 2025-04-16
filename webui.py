import gradio as gr # type: ignore
from Main import *

css = """
footer {visibility: hidden}
"""

# Specify theme to use
theme =  gr.themes.Default(
    primary_hue="rose",
    secondary_hue="rose"
).set(
    color_accent_soft_dark='*primary_800'
)

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
            results = gr.Markdown(
                value="Results will be shown here.",
                line_breaks=True,
                container=True,
                min_height=100
            )
    
    sim_limits.change(update_sim_limits, inputs=[sim_limits], outputs=[sim_time, sim_keys, limit_msg, start_sim])

    start_sim.click(run_sim, inputs=[N, Q, px, sim_time, sim_keys, using_stn, simple, graph, round_time, classic_time], outputs=[results])

if __name__ == "__main__":
    # Allow use on local network, may add flag to either run locally or on network
    app.launch(
        favicon_path='./imgs/favicon.png',
        share=False,
        server_name="0.0.0.0",
        server_port=7861
    )