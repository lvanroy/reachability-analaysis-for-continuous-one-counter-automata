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
                    # if the uniend is stricly below the current interval
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
