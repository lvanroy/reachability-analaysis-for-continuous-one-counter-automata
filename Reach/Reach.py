class Reach:
    def __init__(self):
        self.state = None
        self.reachable_set = list()

    def update_reach(self, val):
        self.reachable_set.append(val)

    def get_reachable_set(self):
        return self.reachable_set
