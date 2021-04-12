class Node:
    def __init__(self, name):
        self.name = name
        self.label = None

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label
