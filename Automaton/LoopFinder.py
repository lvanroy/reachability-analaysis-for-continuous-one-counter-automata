from typing import Dict, List


class LoopFinder:
    def __init__(self, automaton):
        self.automaton = automaton
        self.visited: Dict[str, bool] = dict()
        self.loops: List[List[str]] = list()

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
                if not self.visited[end]:
                    found_paths[end] = current_chain
                else:
                    loop = self.extract_path(end, current_chain)
                    self.loops.append(loop)

            if not found_paths:
                break

            current_node = list(found_paths.keys())[0]
            current_chain = found_paths[current_node]

            found_paths.pop(current_node)
