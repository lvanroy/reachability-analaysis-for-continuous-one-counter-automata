from Automaton.Expression import Expression


class Edge:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.label = None
        self.operation = None

    def set_label(self, label) -> None:
        self.label = label

    def get_label(self) -> str:
        return self.label

    def set_operation(self, operation: Expression):
        self.operation = operation

    def get_operation(self) -> Expression:
        return self.operation

    def __str__(self):
        if self.label is not None:
            return "{} -> {} -> {}".format(self.start, self.label, self.end)
        else:
            return "{} -> {}".format(self.start, self.end)
