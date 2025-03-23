from numpy import sqrt, ceil, log, log2, log10
from scipy.stats import binom

def simple_sim(N, Q, px, sim_time, using_stn):
    """A simple simulator designed for a specific scenario.

    Args:
      N: Number of rounds of communication within the quantum phase of QKD.
      Q: Link-level noise in the system, as a decimal representation of a percentage.
      px: Probability that the X basis is chosen in the quantum phase of QKD.
      sim_time: Amount of time (in sec) that should be simulated in this run.
      using_stn: Whether the simulator is using STNs.
    """
    # Find time required for qubit generation
    photon_gen_rate = 10**9 / 1000.0                    # Pulse rate in miliseconds
    valid_prob = 10**(-3)                               # Probability of valid photon generation
    valid_gen_rate = photon_gen_rate * valid_prob       # Rate of generation of valid qubits, based on pulse rate
    qubit_rate = N / valid_gen_rate                     # Time required to generate N valid qubits
    quantum_time = qubit_rate                           # Time required for quantum phase of QKD

    # Find time required for classical phase of QKD
    classic_time = quantum_time

    # Find time per switch
    round_time = max(quantum_time, classic_time)

    # Define variables to use for key rates
    eps = 10**(-30)
    eps_abort = 10**(-10)
    eps_prime = 10**(-10)
    p = 2   # Number of TNs/STNs in the chain

    # Math required to find key rates
    beta = sqrt(log(2.0 / eps_abort) / (2.0 * N))
    denom = 1 - (2.0 * px * (1 - px)) - beta
    N_tilde = N * denom
    beta_prime = sqrt(log(2.0 / eps_abort) / (2.0 * N_tilde))
    m_0 = N_tilde * (((px**2) / denom) - beta_prime)
    n_0 = N_tilde * (1 - ((px**2) / denom) - beta_prime)
    mu = sqrt(((n_0 + m_0) / (n_0 * m_0)) * ((m_0 + 1) / m_0) * log(2.0 / eps_prime))
    ec_p_TN = Q + mu
    lambda_ec_TN = -(ec_p_TN * log2(ec_p_TN)) - ((1 - ec_p_TN) * log2(1 - ec_p_TN))
    N_0 = N * denom * (1 - (2 * beta_prime))
    delta = sqrt(((N_0 + 2) / (m_0 * N_0)) * log(2 / (eps**2)))

    # Find w_q
    w_q = 0
    p_lim = int(ceil((p + 1) / 2.0))
    for i in range(p_lim):
        cur_k = (2 * i) + 1
        cur_n = p + 1
        cur_p = Q
        w_q += binom.pmf(cur_k, cur_n, cur_p)

    # Find lambda_ec_STN
    ec_p_STN = w_q + delta
    lambda_ec_STN = -(ec_p_STN * log2(ec_p_STN)) - ((1 - ec_p_STN) * log2(1 - ec_p_STN))

    # Find key rates
    key_length_STN = (n_0 * (1 - lambda_ec_STN)) - lambda_ec_STN - (2.0 * log(1.0 / eps))
    key_length_TN = (n_0 * (1 - lambda_ec_TN)) - lambda_ec_TN - (2.0 * log(2.0 / eps_prime))

    # Find values determining when STNs need to act as TNs
    J = int((key_length_TN - log2(N)) / log2(N))
    J_time = J * round_time

    # Find costs
    cost_STN = ((2 * J * N) + (((2 * p) + 2) * N)) / (J * key_length_STN)
    cost_TN = (((2 * p) + 2) * N) / key_length_TN

    # Variables to track statistics
    node_schedule = ['a0', 'a1']                # Schedule of which node has priority for resources
    timers = {'a0': 0, 'a1': float('inf')}      # Timers denoting how much time is left for each user pair's current QKD session
    finished_keys = 0                           # How many keys have finished in total
    user_pair_keys = dict()                     # Dictionary to keep track of keys finished per user pair
    for node in node_schedule:
        user_pair_keys[node] = 0
    total_cost = 0                              # Total accumulated cost
    average_key_rate = 0                        # Average key rate as ratio of key length / N

    # Simulate sim_time total time passing in the simulator
    total_time = 0  # Track how much time has passed
    while total_time < (sim_time * 1000):
        if using_stn:
            # Get current node pair
            cur_node = node_schedule[0]
            timers[cur_node] = (quantum_time + classic_time)

            # Track time passing for normal round
            total_time += round_time
            for node in timers.keys():
                timers[node] -= round_time
                if timers[node] <= 0:
                    timers[node] = 0

                    # Track stats
                    finished_keys += 1
                    user_pair_keys[cur_node] += 1
                    total_cost += cost_STN
                    average_key_rate += ((key_length_STN / N) - average_key_rate) / finished_keys

            # Handle extra time passing for every J'th round
            if (total_time % J_time) == 0:
                # Find extra time passing this round
                ext_time = classic_time
                if (classic_time > quantum_time):
                    ext_time -= (classic_time - quantum_time)

                # Pass extra time
                total_time += ext_time
                for node in timers.keys():
                    timers[node] -= ext_time
                    if timers[node] <= 0:
                        timers[node] = 0

                        # Track stats
                        finished_keys += 1
                        user_pair_keys[cur_node] += 1
                        total_cost += cost_STN
                        average_key_rate += ((key_length_STN / N) - average_key_rate) / finished_keys

            # Switch the order of priority
            node_schedule.append(node_schedule.pop(0))
        else:
            # Get current node pair
            cur_node = node_schedule[0]
            timers[cur_node] = (quantum_time + classic_time)

            # Track time passing for normal round
            total_time += (quantum_time + classic_time)
            for node in timers.keys():
                timers[node] -= (quantum_time + classic_time)
                if timers[node] <= 0:
                    timers[node] = 0

                    # Track stats
                    finished_keys += 1
                    user_pair_keys[cur_node] += 1
                    total_cost += cost_TN
                    average_key_rate += ((key_length_TN / N) - average_key_rate) / finished_keys

            # Switch the order of priority
            node_schedule.append(node_schedule.pop(0))

    sim_output = ""
    if using_stn:
        node_mode = "STN"
    else:
        node_mode = "TN"
    sim_output += f"\n[]-----[ Simulation Information ]-----[]\nNon-user nodes: {node_mode}s\n\nTime simulated: {total_time / 1000:,.2f} sec\nRounds per quantum phase: 10^{log10(N):.0f}\nLink-level noise: {Q * 100:.1f}%\nX-basis probability: {px}\n"
    sim_output += f"\n[]-----[ Efficiency Statistics ]-----[]\nTotal keys generated: {finished_keys:,}\nKeys by user pair:\n"
    for user in user_pair_keys.keys():
        sim_output += f"    {user}-b{user[1]}: {user_pair_keys[user]:,}\n"
    sim_output += f"Average key rate: {average_key_rate:.4f}\nCost incurred: {total_cost:,.0f}\n"

    print(sim_output)