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
      J: Per-neighbor number of rounds before needing to refresh secret key pool with that neighbor.
    """

    def __init__(self, name=None, neighbors=None):
        """Constructor for the subclass STN of class Node.

        Args:
          name: Name/identifier for the node. Defaults to None.
          neighbors: List of neighboring nodes. Defaults to None.
        """
        self.TN_mode = False
        self.J = dict()
        for n in neighbors:
            self.J[n] = 10
        super().__init__(name=name, node_type="STN")
    
    def use_pool_bits(self, neighbor, N):
        """Decrease the number of secret key pool bits for a neighbor, never going below some minimum.

        Args:
          neighbor: The node with which commmunication has taken place.
          N: The number of rounds in the quantum phase of communication.
        
        Returns:
          Keys left before STN must run EC and PA with given neighbor.
        """
        if self.J[neighbor] > 0:
          self.J[neighbor] -= 1
        
        return self.J[neighbor]
    
    def refresh_pool_bits(self, neighbor, N):
      """Increase the number of secret key pool bits for a neighbor to the maximum allowed.

      Args:
        neighbor: The node with which communication has taken place.
        N: The number of rounds in the quantum phase of communication.
      """
      self.J[neighbor] = 10



class QKD_Inst():
    """A class to represent an instance of running e2e QKD.

    Certain aspects should be tracked on a key-by-key basis.
    This class allows interacting with those aspects in a more structured manner.

    Attributes:
      route: List of nodes involved in this QKD instance.
      operation: What operation the QKD instance is currently working on.
      timer: Amount of time left for current operation.
    """

    def __init__(self, route):
        """Constructor for the class QKD_Inst.

        Args:
          route: A list of nodes representing the route used for this QKD instance.
        """
        self.route = route
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