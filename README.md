Run with "python Main.py" <br />
(The above uses TNs, simulates 100,000,000 seconds, uses N of 10^7, Q of 0.02, px of 0.2, and quantum time, classic time, and round time of 10 sec) <br />
(Use "python Main.py --stn" to use the same values but with STNs) <br />

To use the simple simulator, use "python Main.py --simple" <br />

Arguments: <br />
-h, --help <br />
&emsp; Show help options. <br />
-D <br />
&emsp; Print debug messages. <br />
--stn <br />
&emsp; Use simple trusted nodes (STNs) instead of trusted nodes (TNs). <br />
--simple <br />
&emsp; Run the simple simulator, then exit. <br />
--graph <br />
&emsp; Which graph to use for this run. <br />
&emsp; Defaults to 2, to use graph 2. <br />
--sim_time <br />
&emsp; Seconds to be simulated in this run. <br />
&emsp; Defaults to 100,000,000 seconds. <br />
--round_time <br />
&emsp; The amount of time that passes each simulator round. <br />
&emsp; Defaults to -1, to match the quantum time. <br />
--classic_time <br />
&emsp; The amount of time required for the classical phase of QKD. <br />
&emsp; Defaults to -1, to match the quantum time. <br />
--quantum_rounds <br />
&emsp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. <br />
&emsp; Defaults to 10^7 rounds. <br />
--link_noise <br />
&emsp; Link-level noise in the system, represented as a decimal form of a percentage. <br />
&emsp; Defaults to 0.02. <br />
--px <br />
&emsp; Probability for the X basis to be chosen in the quantum phase of QKD. <br />
&emsp; Defaults to 0.2. <br />