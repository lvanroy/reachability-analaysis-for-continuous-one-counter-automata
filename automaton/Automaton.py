from automaton.Node import Node
from automaton.Edge import Edge


class Automaton:
    def __init__(self, name):
        self.name = name        # the name of the automaton
        self.nodes = dict()     # a node name to node object mapping
        self.edges = dict()     # a start node name to edge object mapping

    # -- NODES

    def node_exists(self, node_name):
        return node_name in self.nodes

    def create_new_node(self, node_name):
        self.nodes[node_name] = Node(node_name)

    def add_label_to_node(self, node_name, label):
        self.nodes[node_name].set_label(label)

    def get_nr_of_nodes(self):
        return len(self.nodes)

    def get_node_label(self, node_name):
        return self.nodes[node_name].get_label()

    # -- EDGES

    def edge_exists(self, start, end):
        return start in self.edges and end in self.edges[start]

    def create_new_edge(self, start, end):
        if start not in self.edges:
            self.edges[start] = dict()

        if end not in self.edges[start]:
            self.edges[start][end] = Edge(start, end)

    def add_label_to_edge(self, start, end, label):
        if not self.edge_exists(start, end):
            print("Error: Edge does not exist")
        self.edges[start][end].set_label(label)

    def get_nr_of_edges(self):
        return len(self.edges)

    def get_edge_label(self, start, end):
        return self.edges[start][end].get_label()
