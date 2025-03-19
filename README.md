Run with "python Main.py" <br />

Arguments: <br />
-h, --help <br />
&emsp; Show help options. <br />
-D <br />
&emsp; Print debug messages. <br />
&emsp; Defaults to False.
--sim_time <br />
&emsp; Seconds to be simulated in this run; the final round may run over some ms. <br />
&emsp; Defaults to 100,000 seconds. <br />
--quantum_rounds <br />
&emsp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. <br />
&emsp; Defaults to 10^7 rounds. <br />
--classic_time <br />
&emsp; The amount of time required for the classical phase of QKD. <br />
&emsp; Defaults to 100 miliseconds. <br />
--node_mode <br />
&emsp; Whether the non-user nodes should be trusted nodes (TN) or simple trusted nodes (STN). <br />
&emsp; Defaults to TN.
--link_noise <br />
&emsp; Link-level noise in the system, represented as a decimal form of a percentage. <br />
&emsp; Defaults to 0.02.
--prob_x_basis <br />
&emsp; Probability for the X basis to be chosen in the quantum phase of QKD. <br />
&emsp; Defaults to 0.2.