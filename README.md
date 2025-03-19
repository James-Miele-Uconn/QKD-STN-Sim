Run with "python Main.py" <br />

Arguments: <br />
-h, --help <br />
&emsp; Show help options <br />
--sim_time <br />
&emsp; How many seconds should be simulated in this run; the final round may run over some ms. Defaults to 100 seconds. <br />
--quantum_rounds <br />
&emsp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. Defaults to 10^7 rounds. <br />
--classic_time <br />
&emsp; The amount of time required for the classical phase of QKD. Defaults to 100 miliseconds. <br />
--node_mode <br />
&emsp; Whether the non-user nodes should be trusted nodes (TN) or simple trusted nodes (STN). Defaults to TN.
