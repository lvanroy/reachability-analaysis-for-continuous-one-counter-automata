import operator


class Expression:
    def __init__(self, op, const):
        self.op = op
        self.const = const

        self.op_to_string = {
            operator.le: "<=",
            operator.ge: ">=",
            operator.eq: "=",
            operator.add: "+",
            operator.sub: "-"
        }

    def apply(self, val) -> int:
        return self.op(val, self.const)

    def get_value(self) -> int:
        return self.const

    def get_operation(self):
        return self.op_to_string[self.op]

    def __str__(self):
        return "{}{}".format(
            self.op_to_string[self.op],
            self.const
        )
