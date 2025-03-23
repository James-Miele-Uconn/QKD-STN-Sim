from numpy import log, log2, sqrt, ceil
from scipy.stats import binom

class Node:
    """A class to represent different nodes in a network.

    There are three types of nodes in the QKD network: Users, TNs, and STNs.
    This class allows funcitonality desired at the node level to be implemented in the simulator.

    Attributes:
      name: Identifier for the node.
      node_type: What kind of node this object represents.
      operation: What operation the node is currently working on.
    """

    def __init__(self, name=None, node_type=None):
        """Constructor for the class Node.

        Args:
          name: Name/identifier for the node. Defaults to None.
          node_type: What type of node this instance will be. Defaults to None.
        """
        self.name = name
        self.node_type = node_type
        self.operation = None



class User(Node):
    """A class to represent Users, based on Node objects."""
  
    def __init__(self, name=None):
        """Constructor for the subclass User of class Node.

        Args:
          name: Name/identifier for the node. Defaults to None.
        """
        super().__init__(name=name, node_type="User")



class TN(Node):
    """A class to represent Trusted Nodes, based on Node objects."""
  
    def __init__(self, name=None):
        """Constructor for the subclass TN of class Node.

        Args:
          name: Name/identifier for the node. Defaults to None.
        """
        super().__init__(name=name, node_type="TN")



class STN(Node):
    """A class to represent Simple Trusted Nodes, based on Node objects.

    Attributes:
      TN_mode: Whether or not this node has to run classical operations.
      J_vals: Per-neighbor number of rounds before needing to refresh secret key pool with that neighbor.
    """

    def __init__(self, name=None, neighbors=None, J=None):
        """Constructor for the subclass STN of class Node.

        Args:
          name: Name/identifier for the node. Defaults to None.
          neighbors: List of neighboring nodes. Defaults to None.
          J: Number of keys that can be made with a specific neighbor before needing to run EC and PA. Defaults to None.
        """
        self.TN_mode = False

        # Initialize J values for all neighbors
        self.J_vals = dict()
        for n in neighbors:
            self.J_vals[n] = int(J)   # Floor of J value

        super().__init__(name=name, node_type="STN")
    
    def use_pool_bits(self, neighbor):
        """Decrease the number of keys allowed before needing to run EC and PA, never going below 0.

        Args:
          neighbor: The node with which commmunication has taken place.
        
        Returns:
          Keys left before STN must run EC and PA with given neighbor.
        """
        if self.J_vals[neighbor] > 0:
            self.J_vals[neighbor] -= 1
        
        return self.J_vals[neighbor]
    
    def refresh_pool_bits(self, neighbor, J):
      """Increase the number of keys allowed before needing to run EC and PA back to original value J.

      Args:
        neighbor: The node with which communication has taken place.
        J: Number of keys that can be made with a specific neighbor before needing to run EC and PA
      """
      self.J_vals[neighbor] = int(J)



class QKD_Inst():
    """A class to represent an instance of running e2e QKD.

    Certain aspects should be tracked on a key-by-key basis.
    This class allows interacting with those aspects in a more structured manner.

    Attributes:
      route: List of nodes involved in this QKD instance.
      p: Number of non-user nodes in this QKD instance.
      operation: What operation the QKD instance is currently working on.
      timer: Amount of time left for current operation.
    """

    def __init__(self, route):
        """Constructor for the class QKD_Inst.

        Args:
          route: A list of nodes representing the route used for this QKD instance.
        """
        self.route = route
        self.p = len(route) - 2
        self.operation = None
        self.timer = 0
    
    def dec_timer(self, amount):
        """Decrement the value of the QKD instance's timer by given amount, never going below 0.

        Args:
          amount: The total amount by which to decrease the timer.
        
        Returns:
          Value of timer after modification.
        """

        if (self.timer < amount):
            self.timer = 0
        else:
            self.timer -= amount
        
        return self.timer
    
    def switch_operation(self, timer_val=0):
        """Change operation to next phase, and set timer to reflect new operation.

        Args:
          timer_val: What value to set the timer to. Defaults to 0.
        
        Returns:
          Current operation after switch.
        """
        cur_operation = self.operation
        if cur_operation is None:
            self.operation = "Quantum"
            for node in self.route:
                node.operation = "Quantum"
            self.timer = timer_val
        elif cur_operation == "Quantum":
            self.operation = "Classic"
            for node in self.route:
                node.operation = "Classic"
            self.timer = timer_val
        elif cur_operation == "Classic":
            self.operation = None
            for node in self.route:
                node.operation = None
            self.timer = timer_val
        
        return self.operation
    
    def is_finished(self):
        """Determine if QKD instance has finished.

        Returns:
          Boolean based on if route is empty and operation is None.
        """
        cur_op = self.operation
        route_len = len(self.route)

        return ((cur_op is None) and (route_len == 0))

class Info_Tracker():
    """A class for keeping track of various information across multiple QKD instances.

    Some information for which tracking is desired depends on the QKD instances themselves.
    As such, this class will hold all of the information to be tracked, so the QKD instances only interact with a single instance of this class.

    Attributes:
      finished_keys: Number of keys processed in this run of the simulator.
      total_cost: Total cost incurred for this run of the simulator.
      average_key_rate: Average key rate (key length / qubits sent in quantum phase) for this run of the simulator.
      user_pair_keys: Dictionary containing the number of keys made for each user pair in the network.
      math_vars: Dictionary containing variables used for necessary equations.
      key_length_TN: BB84 key rate for networks using TNs, based on N, Q, and px.
      J: Number of keys that can be made with a specific neighbor before needing to run EC and PA.
    """
    def __init__(self, source_nodes, N, Q, px):
        """Constructor for the class Info_Tracker

        Args:
          source_nodes: List of nodes allowed to start QKD.
          N: Number of rounds of communication within the quantum phase of QKD.
          Q: Link-level noise in the system, as a decimal representation of a percentage.
          px: Probability that the X basis is chosen in the quantum phase of QKD.
        """
        # Stats to track
        self.finished_keys = 0
        self.total_cost = 0
        self.average_key_rate = 0

        # Dictionary to track keys made by specific user pairs
        self.user_pair_keys = dict()
        for node in source_nodes:
            self.user_pair_keys[node] = 0

        # Define variables to use for key rates
        self.m_vars = {'N': N, 'Q': Q, 'px': px, 'eps': 10**(-30), 'eps_abort': 10**(-10), 'eps_prime': 10**(-10)}

        # Math required to find key rates
        self.m_vars['beta'] = sqrt(log(2.0 / self.m_vars['eps_abort']) / (2.0 * N))
        self.m_vars['denom'] = 1 - (2.0 * px * (1 - px)) - self.m_vars['beta']
        self.m_vars['N_tilde'] = N * self.m_vars['denom']
        self.m_vars['beta_prime'] = sqrt(log(2.0 / self.m_vars['eps_abort']) / (2.0 * self.m_vars['N_tilde']))
        self.m_vars['m_0'] = self.m_vars['N_tilde'] * (((px**2) / self.m_vars['denom']) - self.m_vars['beta_prime'])
        self.m_vars['n_0'] = self.m_vars['N_tilde'] * (1 - ((px**2) / self.m_vars['denom']) - self.m_vars['beta_prime'])
        self.m_vars['mu'] = sqrt(((self.m_vars['n_0'] + self.m_vars['m_0']) / (self.m_vars['n_0'] * self.m_vars['m_0'])) * ((self.m_vars['m_0'] + 1) / self.m_vars['m_0']) * log(2.0 / self.m_vars['eps_prime']))
        self.m_vars['ec_p_TN'] = Q + self.m_vars['mu']
        self.m_vars['lambda_ec_TN'] = -(self.m_vars['ec_p_TN'] * log2(self.m_vars['ec_p_TN'])) - ((1 - self.m_vars['ec_p_TN']) * log2(1 - self.m_vars['ec_p_TN']))
        self.m_vars['N_0'] = N * self.m_vars['denom'] * (1 - (2 * self.m_vars['beta_prime']))
        self.m_vars['delta'] = sqrt(((self.m_vars['N_0'] + 2) / (self.m_vars['m_0'] * self.m_vars['N_0'])) * log(2 / (self.m_vars['eps']**2)))

        # Key rates
        self.key_length_TN = (self.m_vars['n_0'] * (1 - self.m_vars['lambda_ec_TN'])) - self.m_vars['lambda_ec_TN'] - (2.0 * log(2.0 / self.m_vars['eps_prime']))

        # Key-rate dependent info
        self.J = (self.key_length_TN - log2(N)) / log2(N)

    def find_key_length(self, p, using_stn):
        """Find the length of the key for a QKD instance with the given number of nodes.

        Args:
          p: Number of non-user nodes in the current QKD instance.
          using_stn: Whether the non-user nodes are STNs.

        Returns:
          The length of the key made by the described QKD instance.
        """
        if using_stn:
            # Find w_q
            w_q = 0
            p_lim = int(ceil((p + 1) / 2.0))
            for i in range(p_lim):
                cur_k = (2 * i) + 1
                cur_n = p + 1
                cur_p = self.m_vars['Q']
                w_q += binom.pmf(cur_k, cur_n, cur_p)

            # Find lambda_ec_STN
            ec_p_STN = w_q + self.m_vars['delta']
            lambda_ec_STN = -(ec_p_STN * log2(ec_p_STN)) - ((1 - ec_p_STN) * log2(1 - ec_p_STN))

            # Find length of key for STN
            key_length = (self.m_vars['n_0'] * (1 - lambda_ec_STN)) - lambda_ec_STN - (2.0 * log(1.0 / self.m_vars['eps']))
            if key_length < 0:
                key_length = 0
        else:
            key_length = self.key_length_TN
        
        return key_length

    def increase_finished_keys(self):
        """Increase the counter tracking the number of keys that have been finished."""
        self.finished_keys += 1
    
    def increase_user_pair_keys(self, source_node):
        """Increase the counter tracking the number of keys that have been finished for a specific user pair.

        Args:
          source_node: The node whose counter should be increased
        """
        self.user_pair_keys[source_node] += 1

    def increase_cost(self, p, key_length, using_stn):
        """Increase the counter tracking the total cost incurred.

        Args:
          p: Number of non-user nodes in the current QKD instance.
          key_length: Length of the key made by the current QKD instance.
          using_stn: Whether the non-user nodes are STNs.
        """
        if using_stn:
            # Find cost for current QKD instance and add it to total cost
            # Assuming EC(N, w(q)) = EC(N, Q) = N
            if key_length == 0:
                cur_cost = float('inf')
            else:
              cur_cost = ((2 * self.J * self.m_vars['N']) + (((2 * p) + 2) * self.m_vars['N'])) / (self.J * key_length)
            self.total_cost += cur_cost
        else:
            # Find cost for current QKD instance and add it to total cost
            # Assuming EC(N, Q) = N
            cur_cost = (((2 * p) + 2) * self.m_vars['N']) / key_length
            self.total_cost += cur_cost
    
    def increase_key_rate(self, key_length):
        """Increase the counter tracking the average key rate.

        Args:
          key_length: Length of the key made by the current QKD instance.
        """
        if self.average_key_rate == 0:
            self.average_key_rate = key_length / self.m_vars['N']
        else:
          self.average_key_rate += ((key_length / self.m_vars['N']) - self.average_key_rate) / self.finished_keys
    
    def increase_all(self, source_node, p, using_stn):
        """Increase all stats that are being tracked.

        Args:
          source_node: The node whose finished key counter should be increased.
          p: Number of non-user nodes in the current QKD instance.
          using_stn: Whether the non-user nodes are STNs.
        """
        self.increase_finished_keys()
        self.increase_user_pair_keys(source_node)
        cur_key_length = self.find_key_length(p, using_stn)
        self.increase_cost(p, cur_key_length, using_stn)
        self.increase_key_rate(cur_key_length)