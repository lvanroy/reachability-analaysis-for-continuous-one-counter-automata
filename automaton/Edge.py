class Edge:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.label = ""

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label
