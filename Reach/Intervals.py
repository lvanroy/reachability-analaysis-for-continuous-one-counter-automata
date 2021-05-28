from typing import List, Type

from Reach.Interval import Interval


class Intervals:
    def __init__(self, low, incl_low, high, incl_high):
        # all the sub-intervals of the current interval
        # we make the assumption that this list is ordered
        # so that the lowest values are first in the list
        # and the highest are last
        self.intervals: List[Interval] = list()

        initial_interval = Interval(low, incl_low, high, incl_high)
        self.intervals.append(initial_interval)

    def get_intervals(self) -> List[Interval]:
        return self.intervals

    def add(self, addends):
        for addend in addends.get_intervals():
            for interval in self.intervals:
                interval.add(addend)

    def union(self, uniends):
        # track if the currently tracked uniend got inserted
        # this is used to verify whether or not the final uniend got added
        inserted = True
        low = None
        incl_low = None
        high = None
        incl_high = None

        for uniend in uniends.get_intervals():
            inserted = False
            low = uniend.get_low_bound()
            incl_low = uniend.is_low_inclusive()
            high = uniend.get_high_bound()
            incl_high = uniend.is_high_inclusive()

            i = -1
            while True:
                i += 1
                if i >= len(self.intervals):
                    break

                interval = self.intervals[i]

                # see if the current interval is completely to the left of the uniend
                if interval.get_high_bound() < low:
                    continue

                # see if the current interval supersedes the uniend
                if interval.get_high_bound() >= high:
                    # if the uniend is strictly below the current interval
                    # we insert the uniend directly below the current interval
                    if interval.get_low_bound() > high:
                        self.intervals.insert(i, Interval(low, incl_low, high, incl_high))
                        inserted = True
                        i += 1
                        break

                    # if the upper bound is overlapping
                    # we simply need to assert that if either one
                    # is inclusive, the interval will reflect this
                    if interval.get_high_bound() == high:
                        if incl_high:
                            interval.set_incl_high(incl_high)

                    # if the lower bound is overlapping
                    # we need to assert whether or not either one is inclusive
                    if interval.get_low_bound() == high:
                        if incl_high or interval.is_low_inclusive():
                            high = interval.get_high_bound()
                            incl_high = interval.is_high_inclusive()
                            self.intervals.pop(i)
                            self.intervals.insert(i, Interval(low, incl_low, high, incl_high))
                            inserted = True
                            break
                        else:
                            self.intervals.insert(i, Interval(low, incl_low, high, incl_high))
                            inserted = True
                            break

                    # the uniend extends the current interval in the lower direction
                    # update the interval to reflect this
                    if interval.get_low_bound() > low:
                        interval.update_low(low, incl_low)

                    # if the lower bound is overlapping
                    # we simply need to assert that if either one
                    # is inclusive, the interval will reflect this
                    elif interval.get_low_bound() == low:
                        if incl_low:
                            interval.set_incl_low(incl_low)

                    inserted = True
                    break

                # see if the uniend supersedes the current interval
                elif interval.get_high_bound() < high:
                    # verify whether or not the two intervals connect
                    if interval.get_high_bound() == low:
                        if interval.is_high_inclusive() or incl_low:
                            low = interval.get_low_bound()
                            incl_low = interval.is_low_inclusive()
                        else:
                            continue

                    # if the current interval extends the uniend in the lower direction
                    # update the uniend to reflect this
                    if interval.get_low_bound() < low:
                        low = interval.get_low_bound()
                        incl_low = interval.is_low_inclusive()

                    # if the lower bound is overlapping
                    # assure that the incl_low variable correctly reflects this
                    elif interval.get_low_bound() == low:
                        incl_low |= interval.is_low_inclusive()

                    self.intervals.pop(i)
                    i -= 1

        if not inserted:
            self.intervals.append(Interval(low, incl_low, high, incl_high))

    def rescale_reach(self, lower_bound, upper_bound):
        i = -1
        while True:
            i += 1

            if i >= len(self.intervals):
                break

            interval = self.intervals[i]

            out_of_bounds = interval.get_low_bound() > upper_bound
            out_of_bounds |= interval.get_high_bound() < lower_bound

            if out_of_bounds:
                self.intervals.pop(i)
                i -= 1
                continue

            interval.rescale_reach(lower_bound, upper_bound)

    def is_expansion_of(self, other_intervals):
        # check if the absolute size of the new interval is equal or larger
        # than the other preceding interval
        difference = 0
        bounds = 0
        for interval in self.intervals:
            difference += interval.get_high_bound()
            difference -= interval.get_low_bound()
            bounds -= (not interval.is_low_inclusive())
            bounds -= (not interval.is_high_inclusive())

        for interval in other_intervals.get_intervals():
            difference -= interval.get_high_bound()
            difference += interval.get_low_bound()
            bounds += (not interval.is_low_inclusive())
            bounds += (not interval.is_high_inclusive())

        if difference == 0:
            is_expansion = bounds >= 0
        else:
            is_expansion = difference > 0

        if not is_expansion:
            return False

        # ensure that the new interval contains the entire preceding interval
        i = 0  # expanded intervals
        j = 0  # preceding intervals
        while True:
            if j >= len(other_intervals.get_intervals()):
                break
            if i >= len(self.intervals):
                break

            old_interval = other_intervals.get_intervals()[j]
            old_low_bound = old_interval.get_low_bound()
            old_high_bound = old_interval.get_high_bound()
            old_incl_low = old_interval.is_low_inclusive()
            old_incl_high = old_interval.is_high_inclusive()

            new_low_bound = self.intervals[i].get_low_bound()
            new_high_bound = self.intervals[i].get_high_bound()
            new_incl_low = self.intervals[i].is_low_inclusive()
            new_incl_high = self.intervals[i].is_high_inclusive()

            if old_low_bound > new_high_bound:
                i += 1
                continue

            if new_low_bound < old_low_bound and new_high_bound > old_high_bound:
                j += 1
                continue

            if new_low_bound == old_low_bound:
                if not new_incl_low and old_incl_low:
                    break

            if new_high_bound == old_high_bound:
                if not new_incl_high and old_incl_high:
                    break

            if old_low_bound < new_low_bound or old_high_bound > new_high_bound:
                break

            j += 1

        return j == len(self.intervals)

    def equals(self, other_intervals):
        if len(self.intervals) != len(other_intervals.get_intervals()):
            return False

        for i in range(len(self.intervals)):
            interval = self.intervals[i]
            other_interval = other_intervals.get_intervals()[i]
            if not interval.equals(other_interval):
                return False

        return True

    def get_inf(self):
        return self.intervals[0].get_low_bound()

    def update_inf(self, inf):
        self.intervals[0].update_low(inf, True)

    def is_inf_inclusive(self):
        return self.intervals[0].is_low_inclusive()

    def update_lower_bound_inclusive(self, inclusive):
        self.intervals[-1].set_incl_low(inclusive)

    def get_sup(self):
        return self.intervals[-1].get_high_bound()

    def is_sup_inclusive(self):
        return self.intervals[-1].is_high_inclusive()

    def update_sup(self, sup):
        self.intervals[-1].update_high(sup, True)

    def update_higher_bound_inclusive(self, inclusive):
        self.intervals[-1].set_incl_high(inclusive)

    def is_empty(self):
        is_empty = True

        for interval in self.intervals:
            if interval.get_low_bound() != interval.get_high_bound():
                is_empty = False
            elif interval.is_low_inclusive() or interval.is_high_inclusive():
                is_empty = False

        return is_empty or len(self.intervals) == 0

    def remove_inconsistencies(self):
        for i in reversed(range(len(self.intervals))):
            interval = self.intervals[i]
            if interval.get_low_bound() == interval.get_high_bound():
                if not interval.is_low_inclusive():
                    self.intervals.pop(i)
                if not interval.is_high_inclusive():
                    self.intervals.pop(i)

    def __str__(self):
        output_str = ""

        for interval in self.intervals:
            if interval.is_low_inclusive():
                output_str += "["
            else:
                output_str += "("

            output_str += "{}, {}".format(interval.get_low_bound(),
                                          interval.get_high_bound())

            if interval.is_high_inclusive():
                output_str += "]"
            else:
                output_str += ")"

            output_str += " "

        return output_str[:-1]
