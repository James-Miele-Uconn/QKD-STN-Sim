Run with "python Main.py"

Arguments:
-h, --help        Show help options
--sim_time        How many seconds should be simulated in this run. Acts as a minimum; the final round may run over by some miliseconds. Defaults to 100 seconds.
--quantum_rounds  Number of rounds for each quantum phase of QKD; should be at least 10^4 to be able to reliably generate keys. Defaults to 10^7 rounds.
--classic_time    The amount of time required for the classical phase of QKD. Defaults to 100 miliseconds.
--node_mode       Whether the non-user nodes in the graph should be trusted nodes (TN) or simple trusted nodes (STN). Defaults to TN.
