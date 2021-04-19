class Edge:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.label = None
        self.operation = None

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def set_operation(self, operation):
        self.operation = operation

    def get_operation(self):
        return self.operation
