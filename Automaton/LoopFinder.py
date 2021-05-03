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
            high_bound = None
            for node in loop.get_nodes():
                condition = self.automaton.get_node_condition(node)
                if condition is None:
                    continue
                operation = condition.get_operation()
                value = condition.get_value()
                if operation == ">=":
                    if low_bound is None or value < low_bound:
                        low_bound = value

                if operation == "<=":
                    if high_bound is None or value > high_bound:
                        high_bound = value

            loop.set_min_bound(low_bound)
            loop.set_max_bound(high_bound)


class Loop:
    def __init__(self, nodes):
        self.nodes: List[str] = nodes
        self.max_bound = None
        self.min_bound = None

    def get_nodes(self):
        return self.nodes

    def set_max_bound(self, max_bound):
        self.max_bound = max_bound

    def set_min_bound(self, min_bound):
        self.min_bound = min_bound
