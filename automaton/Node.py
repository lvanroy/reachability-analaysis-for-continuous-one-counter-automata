class Node:
    def __init__(self, name):
        self.name = name
        self.label = None
        self.condition = None

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def set_condition(self, condition):
        self.condition = condition

    def get_condition(self):
        return self.condition
