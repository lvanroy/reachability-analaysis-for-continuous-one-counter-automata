from automaton.Node import Node
from automaton.Edge import Edge


class Automaton:
    def __init__(self, name):
        self.name = name            # the name of the automaton
        self.nodes = dict()         # a node name to node object mapping
        self.edges = dict()         # a start node name to edge object mapping
        self.initial_node = None    # the initial node of the automaton

    # -- NODES

    def node_exists(self, node_name):
        return node_name in self.nodes

    def create_new_node(self, node_name):
        self.nodes[node_name] = Node(node_name)

    # -- node labels

    def add_label_to_node(self, node_name, label):
        self.nodes[node_name].set_label(label)

    def get_node_label(self, node_name):
        return self.nodes[node_name].get_label()

    # -- node conditions

    def add_condition_to_node(self, node_name, condition):
        self.nodes[node_name].set_condition(condition)

    def get_node_condition(self, node_name):
        return self.nodes[node_name].get_condition()

    # -- node utility

    def get_nr_of_nodes(self):
        return len(self.nodes)

    def set_node_invisible(self, node_name):
        self.nodes[node_name].set_invisible()

    # -- EDGES

    def edge_exists(self, start, end):
        return start in self.edges and end in self.edges[start]

    def create_new_edge(self, start, end):
        if start not in self.edges:
            self.edges[start] = dict()

        if end not in self.edges[start]:
            self.edges[start][end] = Edge(start, end)

    def get_nr_of_edges(self):
        nr_of_edges = 0
        for start in self.edges:
            nr_of_edges += len(self.edges[start])
        return nr_of_edges

    # -- edge labels

    def add_label_to_edge(self, start, end, label):
        self.edges[start][end].set_label(label)

    def get_edge_label(self, start, end):
        return self.edges[start][end].get_label()

    # -- edge operations

    def add_operation_to_edge(self, start, end, operation):
        self.edges[start][end].set_operation(operation)

    def get_edge_operation(self, start, end):
        return self.edges[start][end].get_operation()

    # -- UTILITIES

    def find_initial_node(self):
        invisible_node = None

        for node in self.nodes:
            if self.nodes[node].is_invisible():
                invisible_node = node
                break

        if invisible_node is None or \
                invisible_node not in self.edges:
            print("Error: no initial node was found, "
                  "make sure that there is a node with an "
                  "incoming edge originating from an invisible "
                  "node.")
            exit(-1)

        potential_start_nodes = list(self.edges[invisible_node].values())
        self.initial_node = potential_start_nodes[0]
