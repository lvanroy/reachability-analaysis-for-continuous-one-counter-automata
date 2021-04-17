from automaton.Automaton import Automaton
import operator


class DotReader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.edge_types = ["->", "--"]

        self.ops = {
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "=": operator.eq,
            "!=": operator.ne
        }

    def create_automaton(self):
        with open(self.file_name, "r") as f:
            lines = f.readlines()

            for line in lines:
                tokens = self.generate_tokens(line)

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
                        next_node = tokens[i + 1]
                        nodes.append(next_node)
                        self.add_node(automaton, next_node)
                        self.add_edge(automaton, node, next_node)

                    # register label specification
                    if tokens[i] == "label":
                        label = self.get_label(tokens[i + 1:])
                        if edge:
                            prev_node = nodes[0]
                            for j in range(1, len(nodes)):
                                next_node = nodes[j]
                                self.set_edge_label(automaton, prev_node, next_node, label)
                                prev_node = next_node
                        else:
                            # verify that there is no xlabel given
                            # xlabel should take precedence over normal labels
                            for el in nodes:
                                if self.get_node_label(automaton, el) is None:
                                    self.set_node_label(automaton, el, label)

                    if tokens[i] == "xlabel":
                        label = self.get_label(tokens[i + 1:])
                        for el in nodes:
                            self.set_node_label(automaton, el, label)

        return automaton

    # -- NODE OPERATIONS

    @staticmethod
    def add_node(automaton, node_name):
        if not automaton.node_exists(node_name):
            automaton.create_new_node(node_name)

    @staticmethod
    def set_node_label(automaton, node, label):
        automaton.add_label_to_node(node, label)

    @staticmethod
    def get_node_label(automaton, node):
        automaton.get_node_label(node)

    # -- EDGE OPERATIONS

    @staticmethod
    def add_edge(automaton, node, next_node):
        automaton.create_new_edge(node, next_node)

    @staticmethod
    def set_edge_label(automaton, prev_node, next_node, label):
        automaton.add_label_to_edge(prev_node, next_node, label)

    # -- LABEL OPERATIONS

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

    def convert_label_to_lambda(self, label):
        expressions = list()

        constant = ""
        op = ""

        for char in label:
            if char.isnumeric() or char in ['+', '-']:
                constant += char
            else:
                op += char

        f = None
        if op in self.ops:
            f = Expression(operator.le, float(constant))
        else:
            print("Error: no matching lambda function "
                  "found for expression {}".format(op))
            exit(-1)

        expressions.append(f)
        return expressions

    # -- UTILITY FUNCTIONS

    def generate_tokens(self, line):
        line = line.lstrip()

        if line[-1] == ";":
            line = line[:-1]

        # track whether or not we are defining a literal string
        string_def = False
        for i in range(len(line)):
            char = line[i]
            if char == '"':
                string_def = not string_def

            if string_def:
                continue

            if char in ['[', ']', '=']:
                line = self.replace_str_index(line, i, ' ')
                continue

            if char in ['\r', '\n']:
                line = self.replace_str_index(line, i, '')

        tokens = line.split(" ")

        return tokens

    @staticmethod
    def replace_str_index(text, index, replacement):
        return "{}{}{}".format(
            text[:index],
            replacement,
            text[index + 1:]
        )


class Expression:
    def __init__(self, op, const):
        self.op = op
        self.const = const

    def apply(self, val):
        return self.op(val, self.const)
