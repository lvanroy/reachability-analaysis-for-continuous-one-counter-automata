from automaton.Automaton import Automaton
import re


class DotReader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.edge_types = ["->", "--"]

    def create_automaton(self):
        with open(self.file_name, "r") as f:
            lines = f.readlines()

            for line in lines:
                tokens = re.split(r' |[|]|=', line.lstrip())

                # start of a graph
                if tokens[0] == "digraph":
                    automaton_name = tokens[1].replace("{", "")
                    automaton = Automaton(automaton_name)
                    continue

                # end of a graph
                if tokens[0] == "}":
                    break

                # read out edge information
                node = tokens[0]
                self.add_node(automaton, node)

                for i in range(1, len(tokens), 2):
                    if tokens[i] in self.edge_types:
                        next_node = tokens[i+1]
                        self.add_node(automaton, next_node)
                        self.add_edge(automaton, node, next_node)

        return automaton

    @staticmethod
    def add_node(automaton, node_name):
        if not automaton.node_exists(node_name):
            automaton.create_new_node(node_name)

    @staticmethod
    def add_edge(automaton, node, next_node):
        automaton.create_new_edge(node, next_node)
