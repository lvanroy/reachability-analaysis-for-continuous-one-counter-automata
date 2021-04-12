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
                line = line\
                    .lstrip()\
                    .replace("\r", "")\
                    .replace("\n", "")

                if line[-1] == ";":
                    line = line[:-1]

                tokens = re.split(r'[ \[\]=]', line.lstrip())

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

                # track the nodes that were discovered within this line
                nodes = [node]

                # register if we are dealing with an edge
                edge = False

                for i in range(1, len(tokens), 2):
                    # register an edge definition
                    if tokens[i] in self.edge_types:
                        edge = True
                        next_node = tokens[i+1]
                        nodes.append(next_node)
                        self.add_node(automaton, next_node)
                        self.add_edge(automaton, node, next_node)

                    # register label specification
                    if tokens[i] == "label":
                        label = self.get_label(tokens[i+1:])
                        if edge:
                            prev_node = nodes[0]
                            for j in range(1, len(nodes)):
                                next_node = nodes[j]
                                automaton.add_label_to_edge(prev_node, next_node, label)
                                prev_node = next_node

                        else:
                            for el in nodes:
                                self.set_node_label(automaton, el, label)

        return automaton

    @staticmethod
    def add_node(automaton, node_name):
        if not automaton.node_exists(node_name):
            automaton.create_new_node(node_name)

    @staticmethod
    def add_edge(automaton, node, next_node):
        automaton.create_new_edge(node, next_node)

    @staticmethod
    def set_node_label(automaton, node, label):
        automaton.add_label_to_node(node, label)

    @staticmethod
    def get_label(tokens):
        delimiter = tokens[0][0]
        label = tokens[0].replace(delimiter, "", 1)
        while True:
            nr_of_delimiters = label.count(delimiter)
            nr_of_escaped_delimiters = label.count("\\" + delimiter)
            if nr_of_delimiters - nr_of_escaped_delimiters == 1:
                break
            label += " {}".format(tokens.pop(1))

        tokens[0] = delimiter + label
        return ''.join(label.rsplit(delimiter, 1))
