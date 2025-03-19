Run with "python Main.py" <br />

Arguments: <br />
-h, --help &emsp;&ensp; Show help options <br />
--sim_time &emsp;&ensp; How many seconds should be simulated in this run; the final round may run over some ms. Defaults to 100 seconds. <br />
--quantum_rounds &emsp;&ensp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. Defaults to 10^7 rounds. <br />
--classic_time &emsp;&ensp; The amount of time required for the classical phase of QKD. Defaults to 100 miliseconds. <br />
--node_mode &emsp;&ensp; Whether the non-user nodes in the graph should be trusted nodes (TN) or simple trusted nodes (STN). Defaults to TN.
