from typing import Dict, List

from Automaton.Node import Node
from Automaton.Edge import Edge
from Automaton.Expression import Expression
from Automaton.LoopFinder import LoopFinder, Loop


class Automaton:
    def __init__(self, name, low, high):
        self.name = name                      # the name of the Automaton
        self.nodes = dict()                   # a node name to node object mapping
        self.edges = dict()                   # a start node name to edge object mapping
        self.initial_node = None              # the initial node of the Automaton
        self.lower_bound = low                # the lower bound of the Automaton
        self.upper_bound = high               # the upper bound of the Automaton
        self.loops: List[Loop] = list()       # the loops within the Automaton
        self.initial_value = 0                # the initial counter value

    # -- NODES

    def node_exists(self, node_name) -> bool:
        return node_name in self.nodes

    def create_new_node(self, node_name):
        self.nodes[node_name] = Node(node_name)
        return self

    def get_node(self, node_name) -> Node:
        if node_name in self.nodes:
            return self.nodes[node_name]

    # -- node labels

    def add_label_to_node(self, node_name, label) -> None:
        self.nodes[node_name].set_label(label)

    def get_node_label(self, node_name) -> bool:
        return self.nodes[node_name].get_label()

    # -- node conditions

    def add_condition_to_node(self, node_name, condition):
        self.nodes[node_name].set_condition(condition)

    def get_node_condition(self, node_name) -> Expression:
        return self.nodes[node_name].get_condition()

    # -- node utility

    def get_nr_of_nodes(self) -> int:
        return len(self.nodes)

    def set_node_invisible(self, node_name):
        self.nodes[node_name].set_invisible()

    def get_nodes(self) -> Dict[str, Node]:
        return self.nodes

    def is_initial(self, node) -> bool:
        return self.initial_node == node

    def is_invisible(self, node) -> bool:
        return self.nodes[node].is_invisible()

    # -- EDGES

    def edge_exists(self, start, end) -> bool:
        return start in self.edges and end in self.edges[start]

    def create_new_edge(self, start, end):
        if start not in self.edges:
            self.edges[start] = dict()

        if end not in self.edges[start]:
            self.edges[start][end] = Edge(start, end)

        return self

    def move_edge_start(self, old_start, new_start):
        if old_start in self.edges:
            if new_start not in self.edges:
                self.edges[new_start] = dict()
            keys = list(self.edges[old_start].keys())
            for end_node in keys:
                edge = self.edges[old_start].pop(end_node)
                self.edges[new_start][end_node] = edge
                edge.set_start(new_start)

    def get_nr_of_edges(self) -> int:
        nr_of_edges = 0
        for start in self.edges:
            nr_of_edges += len(self.edges[start])
        return nr_of_edges

    def get_proceeding_edges(self, end) -> Dict[str, List[Edge]]:
        result: Dict[str, List[Edge]] = dict()
        for start in self.edges:
            if end in self.edges[start]:
                if start not in result:
                    result[start] = list()
                result[start].append(self.edges[start][end])
        return result

    def get_outgoing_edges(self, start) -> Dict[str, Edge]:
        if start in self.edges:
            return self.edges[start]
        else:
            return dict()

    def get_edge(self, start, end) -> Edge:
        if start in self.edges:
            if end in self.edges[start]:
                return self.edges[start][end]

    def remove_edge(self, start, end):
        if start in self.edges:
            if end in self.edges[start]:
                self.edges[start].pop(end)

    # -- edge labels

    def add_label_to_edge(self, start, end, label):
        self.edges[start][end].set_label(label)

    def get_edge_label(self, start, end) -> str:
        return self.edges[start][end].get_label()

    # -- edge operations

    def add_operation_to_edge(self, start, end, operation):
        self.edges[start][end].set_operation(operation)

    def get_edge_operation(self, start, end) -> Expression:
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

        potential_start_nodes = list(self.edges[invisible_node].keys())
        self.initial_node = potential_start_nodes[0]

    def get_initial_node(self):
        return self.initial_node

    def get_lower_bound(self) -> float:
        return self.lower_bound

    def set_lower_bound(self, bound):
        self.lower_bound = bound

    def set_upper_bound(self, bound):
        self.upper_bound = bound

    def get_upper_bound(self) -> float:
        return self.upper_bound

    def initialize_loops(self):
        loop_finder = LoopFinder(self)
        loop_finder.find_loops()
        self.loops = loop_finder.get_loops()

    def get_loops(self) -> List[Loop]:
        return self.loops

    def set_initial_value(self, initial):
        self.initial_value = initial

    def get_initial_value(self):
        return self.initial_value
