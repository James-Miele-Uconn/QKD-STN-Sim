# QKD STN vs TN Network Simulator

This project attempted to create a simulator to show the differences between using trusted nodes (TNs) and simple trusted nodes (STNs) in a network for quantum key distribution.
To run the web-based UI, use webui-user.bat. <br />

# Overview of Use

The webui is split into three parts: the left column which contains modifiable settings for the network, the middle column containg the graph preview and purge options, and the right column with control over the simulator and the results.

# Left Column Explanation

The left column contains the settings that can be changed to modify the state of the network. The first set of options is general options about the simulator itself. The first checkbox determines whether TNs will be used (not checked) or STNs will be used (checked). The second set of checkboxes indicate termination values to end the simulator. You can choose how much time to simulate, how many keys to simulate, or both, in which case the first value met will end the simulation. At least one value must be selected, and the "Run Simulation" button becomes non-interactive if neither is checked. To prevent infinite loops, if only the keys are selected as the terminating value, the simulation will end if none of the user pairs have made a key after five attempts each.

The next set of options involves the network graph to be used. Some graphs are predefined, these being Chain graphs, Specific graphs, and Random graphs. The Chain graphs split the user pairs in two and place a chain of non-user nodes between them. The Specific graphs are the graphs I specified for testing during devlopment. The Random graphs currently only support specific sizes of random 2d grid graphs. The Graph option allows choosing the specific graph of the graph type, and the number of user pairs in the network can be specified.

Instead of using the above predefined options, a text file containing a dict of dicts for the network graph can be provided, with some limitations. Specifically, it must be a dict of dicts, and it mus follow the logic I used for the graphs: users are always entered in correlated pairs, the source users are entered as lowercase "a" and some number, a corresponding destination user must be entered as lowercase "b" and the same number, and any non-user nodes must be entered as lowercase "n" and some number.

The next set of options allows control over some timing for the simulator. The simulator works in rounds, with each round representing some amount of time passing. This value can be specififed by the user, or if -1 is used, the value used will be the minimum of the time required for the quantum phase and the time required for the classical phase. The latter of these can similarly be specified, and similarly has a default value which uses an equation to optimize this value under a certain assumption: if there is an STN node in a network that all routes must use at some point, an equation is used ot determine the length of time for the classical phase to allow 100% efficiency for said node.

The next set of options are mostly for the equations used to track statistics, but have some overlap with other portions of the simulator. N is the number of rounds in the quantum phase, Q is the link-level noise (as a decimal representation of a percentage), px is the probability of choosing the X-basis in the quantum phase.

There is also limited support for batch runs of the simulator. Some of the variables have been specified, and can be chosen from the dropdown lists on the left. Different values for the chosen variable can then be entered as a comma-separated list on the right side, and the simulator will loop through using these alternate values, saving all results to a csv file. If only one variable is being changed, the top row must be used, and if two variables are being changed, the top two rows must be used.

# Middle Column Explanation

When the network graph is made for the simulation, an image for that graph is saved to a directory in the project. At the same time, a text file containing the dict of dicts for the graph is saved in the same directory. After the simulation ends, the image for the graph is shown to the user. Since the simulator may be run several times in quick succession, there is a button to remove the directory containing the graph images and dict of dicts text files.

# Right Column Explanation

The "Run Simulation" button will run the simualtion with the current values specified by the left column. After the simulation ends, the results are saved to a csv file. If batch options were not used, a formatted version of the results will be displayed in the "Results will be shown here." area; if batch options are used, this area will instead state that the results can be found in the csv file. In a similar manner to the graphs, since many csv files may be made in a short amount of time, a button is provided to remove the directory containing these files.

# Customization Sidebar Explanation

The customization options are currently held in a collapsable sidebar; click the arrow on the top right of the screen to show/hide these options. The first option allows switching between light-mode and dark-mode. The default mode will be based on your browser's preference, but a button is provided to allow switching between these two modes.

There are some options that require the webui server to restart in order to take effect. Currently, this is only the color to use for the UI. To change this option, select the desirec color using the dropdown menu, press the "Reload UI" button, and refresh the tab.



<sup><sub>Favicon from: <a href="https://www.flaticon.com/free-icons/quantum" title="quantum icons">Quantum icons created by Triangle Squad - Flaticon</a></sub></sup>