from typing import Dict, List


class LoopFinder:
    def __init__(self, automaton):
        self.automaton = automaton
        self.visited: Dict[str, bool] = dict()
        self.loops: List[Loop] = list()

        self.initialize_visited()

    def initialize_visited(self):
        nodes = self.automaton.get_nodes()
        for node in nodes:
            self.visited[node] = False

    @staticmethod
    def extract_path(start, path):
        for i in reversed(range(len(path))):
            if path[i] == start:
                return path[i:]

    def get_loops(self):
        return self.loops

    def find_loops(self):
        current_node = self.automaton.get_initial_node()
        current_chain = list()
        found_paths: Dict[str, List[str]] = dict()

        while True:
            self.visited[current_node] = True
            current_chain.append(current_node)

            for end in self.automaton.get_outgoing_edges(current_node):
                if end not in current_chain:
                    found_paths[end] = current_chain.copy()
                else:
                    loop_path = self.extract_path(end, current_chain)
                    self.loops.append(Loop(loop_path))

            if not found_paths:
                break

            current_node = list(found_paths.keys())[0]
            current_chain = found_paths[current_node]

            found_paths.pop(current_node)

        for loop in self.loops:
            low_bound = None
            low_bound_node = None
            low_preceding_node = None

            high_bound = None
            high_bound_node = None
            high_preceding_node = None

            contains_sub = False
            contains_add = False

            nodes = loop.get_nodes()
            for i in range(len(nodes)):
                node = nodes[i]
                next_node = nodes[(i + 1) % len(nodes)]

                edge = self.automaton.get_outgoing_edges(node)[next_node]
                operation = str(edge.get_operation())

                if operation == "None" or \
                        operation == "+0" or \
                        operation == "-0":
                    pass
                elif operation[0] == "+":
                    contains_add = True
                elif operation[0] == "-":
                    contains_sub = True

                condition = self.automaton.get_node_condition(node)
                if condition is None:
                    continue
                operation = condition.get_operation()
                value = condition.get_value()
                if operation == ">=":
                    if low_bound is None or value < low_bound:
                        low_bound = value
                        low_bound_node = node
                        low_preceding_node = nodes[i-1]

                if operation == "<=":
                    if high_bound is None or value > high_bound:
                        high_bound = value
                        high_bound_node = node
                        high_preceding_node = nodes[i-1]

            loop.set_min_bound(low_bound)
            loop.set_min_bounded_node(low_bound_node)
            loop.set_max_preceding_node(low_preceding_node)

            loop.set_max_bound(high_bound)
            loop.set_max_bounded_node(high_bound_node)
            loop.set_max_preceding_node(high_preceding_node)

            loop.register_addition(contains_add)
            loop.register_subtraction(contains_sub)


class Loop:
    def __init__(self, nodes):
        self.nodes: List[str] = nodes

        self.max_bound = None
        self.max_bounded_node = None
        self.max_preceding_node = None

        self.min_bound = None
        self.min_bounded_node = None
        self.min_preceding_node = None

        self.expanded_up = False
        self.expanded_down = False

        self.contains_sub = False
        self.contains_add = False

    def get_nodes(self):
        return self.nodes

    def set_max_bound(self, max_bound):
        self.max_bound = max_bound

    def get_max_bound(self):
        return self.max_bound

    def set_max_bounded_node(self, node):
        self.max_bounded_node = node

    def get_max_bounded_node(self):
        return self.max_bounded_node

    def set_max_preceding_node(self, node):
        self.max_preceding_node = node

    def get_max_preceding_node(self):
        return self.max_preceding_node

    def set_min_bound(self, min_bound):
        self.min_bound = min_bound

    def get_min_bound(self):
        return self.min_bound

    def set_min_bounded_node(self, node):
        self.min_bounded_node = node

    def get_min_bounded_node(self):
        return self.min_bounded_node

    def set_min_preceding_node(self, node):
        self.min_preceding_node = node

    def get_min_preceding_node(self):
        return self.min_preceding_node

    def register_upwards_expansion(self):
        self.expanded_up = True

    def has_upwards_expanded(self):
        return self.expanded_up

    def register_downwards_expansion(self):
        self.expanded_down = True

    def has_downwards_expanded(self):
        return self.expanded_down

    def register_addition(self, value):
        self.contains_add = value

    def has_add(self):
        return self.contains_add

    def register_subtraction(self, value):
        self.contains_sub = value

    def has_sub(self):
        return self.contains_sub

    def __str__(self):
        output = ""
        for node in self.nodes:
            output += "{}, ".format(node)
        output += self.nodes[0]
        return output
