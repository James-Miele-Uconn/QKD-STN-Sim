# QKD STN vs TN Network Simulator

To run the web-based UI, use webui-user.bat. <br />
Alternatively, for the command-line version use "python Main.py". <br />

Arguments for the command-line version file: <br />
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
&emsp; Seconds to be simulated in this run, set to -1 to disable. <br />
&emsp; Defaults to 100,000,000 seconds. <br />
--sim_keys <br />
&emsp; Keys to be simulated in this run, set to -1 to disable. <br />
&emsp; Defaults to -1. <br />
--round_time <br />
&emsp; The amount of time that passes each simulator round. <br />
&emsp; Defaults to -1, to match the quantum time. <br />
--classic_time <br />
&emsp; The amount of time required for the classical phase of QKD. <br />
&emsp; Defaults to -1, to match the quantum time. <br />
--N <br />
&emsp; Number of rounds for each quantum phase of QKD; should be at least 10^4 rounds. <br />
&emsp; Defaults to 10^7 rounds. <br />
--Q <br />
&emsp; Link-level noise in the system, represented as a decimal form of a percentage. <br />
&emsp; Defaults to 0.02. <br />
--px <br />
&emsp; Probability for the X basis to be chosen in the quantum phase of QKD. <br />
&emsp; Defaults to 0.2. <br />