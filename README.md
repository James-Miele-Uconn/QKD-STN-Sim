Run with "python Main.py" <br />

Arguments: <br />
-h, --help <br />
&emsp; Show help options. <br />
--sim_time <br />
&emsp; Seconds to be simulated in this run; the final round may run over some ms. <br />
&emsp; Defaults to 100 seconds. <br />
--quantum_rounds <br />
&emsp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. <br />
&emsp; Defaults to 10^7 rounds. <br />
--classic_time <br />
&emsp; The amount of time required for the classical phase of QKD. <br />
&emsp; Defaults to 100 miliseconds. <br />
--node_mode <br />
&emsp; Whether the non-user nodes should be trusted nodes (TN) or simple trusted nodes (STN). <br />
&emsp;Defaults to TN.
