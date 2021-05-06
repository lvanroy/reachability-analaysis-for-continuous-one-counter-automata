class Node:
    def __init__(self, name):
        self.name = name
        self.label = None
        self.condition = None
        self.invisible = False

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def set_condition(self, condition):
        self.condition = condition

    def get_condition(self):
        return self.condition

    def set_invisible(self):
        self.invisible = True

    def is_invisible(self):
        return self.invisible

    def get_name(self):
        return self.name

    def __str__(self):
        if self.condition is not None:
            return "{} [{}]".format(self.name, self.condition)
        else:
            return "{}".format(self.name)
