import operator
import re

from typing import List

from Automaton.Automaton import Automaton
from Automaton.Expression import Expression
from Automaton.Node import Node
from Automaton.Edge import Edge


class DotReader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.edge_types = ["->", "--"]
        self.automaton = None

        # keep track of the number of newly added nodes/edges
        # this is to provide an easy way to generate unique names
        self.new_node_counter = 0

        self.ops = {
            "<=": operator.le,
            ">=": operator.ge,
            "=": operator.eq,
            "+": operator.add,
            "-": operator.sub
        }

        self.operation_matcher = re.compile(
            r'([+-][0-9]+\n?)+'
        )

        self.condition_matcher = re.compile(
            r'((<=|>=|=)[+-]?[0-9]+\n?)+'
        )

        # keep track of the nodes and edges with incorrect specifications
        # these will be handled after the generation as to ensure that all
        # outgoing and incoming edges are pointing to the new nodes
        self.operational_nodes: List[Node] = list()
        self.conditional_edges: List[Edge] = list()

    def create_automaton(self):
        with open(self.file_name, "r") as f:
            lines = f.readlines()

            for index in range(len(lines)):
                line = lines[index]
                tokens = self.generate_tokens(line)

                if len(tokens) == 0:
                    continue

                tokens = list(filter(lambda x: x != "", tokens))

                # start of a graph
                if tokens[0] == "digraph":
                    automaton_name = tokens[1].replace("{", "")
                    self.automaton = Automaton(automaton_name, float("-inf"), float("inf"))
                    continue

                # if a rankdir is specified, just continue
                if tokens[0] == "rankdir":
                    continue

                # end of a graph
                if tokens[0] == "}":
                    break

                nodes = list()

                edge = False

                i = -1
                while True:
                    i += 1
                    if i >= len(tokens):
                        break

                    # register an edge definition
                    if tokens[i] in self.edge_types:
                        edge = True

                        i += 1
                        next_node = tokens[i]

                        nodes.append(next_node)
                        self.add_node(next_node)
                        self.add_edge(node, next_node)

                        node = next_node

                    # register label specification
                    elif tokens[i] in ["label", "xlabel"]:
                        label = self.get_label(tokens, i+1)

                        # ensure that we do not evaluate the label again
                        i += 1

                        # verify whether or not we are dealing with an expression
                        expression = None
                        is_condition = False
                        if self.operation_matcher.match(label):
                            expression = self.convert_label_to_expression(label)[0]
                        if self.condition_matcher.match(label):
                            expression = self.convert_label_to_expression(label)[0]
                            is_condition = True

                        if edge:
                            # if is_condition is true, expression must be
                            # true too so need to do an extra evaluation
                            # insert an extra node to which we will attach the condition
                            if is_condition:
                                prev_node = nodes[0]
                                for j in range(1, len(nodes)):
                                    next_node = nodes[j]

                                    self.set_edge_operation(prev_node, next_node, expression)
                                    edge = self.get_edge(prev_node, next_node)
                                    self.conditional_edges.append(edge)

                                    prev_node = next_node

                            # if the expression is an operation we can simply add
                            # the expression to the edge
                            else:
                                prev_node = nodes[0]
                                for j in range(1, len(nodes)):
                                    next_node = nodes[j]

                                    if expression is not None:
                                        self.set_edge_operation(prev_node, next_node, expression)
                                    else:
                                        self.set_edge_label(prev_node, next_node, label)

                                    prev_node = next_node
                        else:
                            # if we  did encounter an expression that was
                            # not a condition we will add an edge and a secondary node
                            # we will attach the found expression to the found edge
                            if expression is not None and not is_condition:
                                self.set_node_condition(node, expression)
                                node_obj = self.get_node(node)
                                self.operational_nodes.append(node_obj)

                            elif expression is not None:
                                self.set_node_condition(node, expression)

                            else:
                                self.set_node_label(node, label)

                    # register type specification
                    elif tokens[i] == "style":
                        style = tokens[i + 1]

                        # ensure that we do not evaluate the style token again
                        i += 1

                        if style == "invis":
                            for el in nodes:
                                self.set_node_invisible(el)

                    elif tokens[i] == "shape":
                        # skip the actual shape attribute value
                        i += 1

                        continue

                    # if none of the above we have found a node
                    else:
                        # read out edge information
                        node = tokens[i]
                        self.add_node(node)

                        # track the nodes that were discovered within this line
                        nodes.append(node)

        for edge in self.conditional_edges:
            prev_node = edge.get_start()
            next_node = edge.get_end()
            expression = edge.get_operation()
            self.set_edge_operation(prev_node, next_node, None)

            in_between_node = "_{}".format(self.new_node_counter)
            self.new_node_counter += 1

            self.add_node(in_between_node)
            self.add_edge(prev_node, in_between_node)
            self.add_edge(in_between_node, next_node)
            self.set_node_condition(in_between_node, expression)
            self.remove_edge(prev_node, next_node)

        for node in self.operational_nodes:
            node_name = node.get_name()
            expression = node.get_condition()
            self.set_node_condition(node_name, None)

            in_between_node = "_{}".format(self.new_node_counter)
            self.new_node_counter += 1

            self.move_edge_start(node_name, in_between_node)

            self.add_node(in_between_node)
            self.add_edge(node_name, in_between_node)
            self.set_edge_operation(node_name, in_between_node, expression)

        # find the initial node of the Automaton
        # if multiple nodes can be considered a random
        # node will be selected
        # if no nodes can be considered as the initial node
        # the program will exit
        self.find_initial_node()

        self.automaton.initialize_loops()

        return self.automaton

    # -- NODE OPERATIONS

    def add_node(self, node_name):
        if not self.automaton.node_exists(node_name):
            self.automaton.create_new_node(node_name)

    def set_node_label(self, node, label):
        self.automaton.add_label_to_node(node, label)

    def set_node_condition(self, node, label):
        self.automaton.add_condition_to_node(node, label)

    def set_node_invisible(self, node):
        self.automaton.set_node_invisible(node)

    def get_node(self, node_name) -> Node:
        return self.automaton.get_node(node_name)

    # -- EDGE OPERATIONS

    def add_edge(self, node, next_node):
        self.automaton.create_new_edge(node, next_node)

    def set_edge_label(self, prev_node, next_node, label):
        self.automaton.add_label_to_edge(prev_node, next_node, label)

    def set_edge_operation(self, prev_node, next_node, label):
        self.automaton.add_operation_to_edge(prev_node, next_node, label)

    def remove_edge(self, start, end):
        self.automaton.remove_edge(start, end)

    def get_edge(self, start, end) -> Edge:
        return self.automaton.get_edge(start, end)

    def move_edge_start(self, old_start, new_start):
        self.automaton.move_edge_start(old_start, new_start)

    # -- LABEL OPERATIONS

    @staticmethod
    def get_label(tokens, i):
        delimiter = tokens[i][0]
        label = tokens[i].replace(delimiter, "", 1)
        while True:
            nr_of_delimiters = label.count(delimiter)
            nr_of_escaped_delimiters = label.count("\\" + delimiter)
            if nr_of_delimiters - nr_of_escaped_delimiters == 1:
                break
            label += " {}".format(tokens.pop(i+1))

        tokens[i] = delimiter + label
        return ''.join(label.rsplit(delimiter, 1))

    def convert_label_to_expression(self, label):
        expressions = list()

        # iterate over all subexpressions part of the label
        for sub_expr in label.split("\n"):
            constant = ""
            op = ""

            # iterate over the different characters within the label
            # differentiate between constant and expression
            for char in sub_expr:
                if char.isnumeric() or (char in ["+", "-"] and op != ""):
                    constant += char
                else:
                    op += char

            # create an expression
            f = Expression(self.ops[op], int(constant))

            expressions.append(f)

        return expressions

    # -- UTILITY FUNCTIONS

    def generate_tokens(self, line):
        line = line.lstrip()

        if line == "":
            return list()

        # track whether or not we are defining a literal string
        string_def = False
        for i in reversed(range(len(line))):
            char = line[i]
            if char == '"':
                string_def = not string_def

            if string_def:
                continue

            if char == ',':
                # if we have a comma followed by a space
                # simply remove the comma as it will be properly split
                # in tokens as is
                if line[i+1] == ' ':
                    line = self.replace_str_index(line, i, '')
                # if we do not have a space after the comma
                # replace the comma by a space so that the tokens are properly split again
                else:
                    line = self.replace_str_index(line, i, ' ')

            if char in ['[', ']', '=']:
                line = self.replace_str_index(line, i, ' ')
                continue

            if char in ['\r', '\n']:
                line = self.replace_str_index(line, i, '')

        if line[-1] == ";":
            line = line[:-1]

        tokens = line.split(" ")

        return tokens

    # utility function which allows us to easily replace a character
    # in a string at a given index
    @staticmethod
    def replace_str_index(text, index, replacement):
        return "{}{}{}".format(
            text[:index],
            replacement,
            text[index + 1:]
        )

    def find_initial_node(self):
        self.automaton.find_initial_node()
