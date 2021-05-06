class Interval:
    def __init__(self, low, incl_low, high, incl_high):
        self.low = low
        self.incl_low = incl_low
        self.high = high
        self.incl_high = incl_high

    def get_low_bound(self) -> float:
        return self.low

    def is_low_inclusive(self) -> bool:
        return self.incl_low

    def get_high_bound(self) -> float:
        return self.high

    def is_high_inclusive(self) -> bool:
        return self.incl_high

    def add(self, interval):
        self.low += interval.get_low_bound()
        self.high += interval.get_high_bound()
        self.incl_low &= interval.is_low_inclusive()
        self.incl_high &= interval.is_high_inclusive()

    # def union(self, interval):

    def rescale_reach(self, lower_bound, upper_bound):
        self.high = min(upper_bound, self.high)
        self.high = max(lower_bound, self.high)

        self.low = max(lower_bound, self.low)
        self.low = min(upper_bound, self.low)

    def update_low(self, new_low, new_incl_low):
        self.low = new_low
        self.incl_low = new_incl_low

    def update_high(self, new_high, new_incl_high):
        self.high = new_high
        self.incl_high = new_incl_high

    def set_incl_low(self, new_incl_low):
        self.incl_low = new_incl_low

    def set_incl_high(self, new_incl_high):
        self.incl_high = new_incl_high

    def equals(self, other_interval):
        if self.low != other_interval.get_low_bound():
            return False

        if self.incl_low != other_interval.is_low_inclusive():
            return False

        if self.high != other_interval.get_high_bound():
            return False

        if self.incl_high != other_interval.is_high_inclusive():
            return False

        return True

    def __str__(self):
        output_str = ""

        if self.incl_low:
            output_str += "["
        else:
            output_str += "("

        output_str += "{}, {}".format(self.low, self.high)

        if self.incl_high:
            output_str += "]"
        else:
            output_str += ")"

        return output_str
