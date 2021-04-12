from automaton.Node import Node
from automaton.Edge import Edge


class Automaton:
    def __init__(self, name):
        self.name = name        # the name of the automaton
        self.nodes = dict()     # a node name to node object mapping
        self.edges = dict()     # a start node name to edge object mapping

    def node_exists(self, node_name):
        return node_name in self.nodes

    def create_new_node(self, node_name):
        self.nodes[node_name] = Node(node_name)

    def get_nr_of_nodes(self):
        return len(self.nodes)

    def create_new_edge(self, start, end):
        if start not in self.edges:
            self.edges[start] = dict()

        if end not in self.edges[start]:
            self.edges[start][end] = Edge(start, end)
