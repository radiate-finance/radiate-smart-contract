import smartpy as sp

class Calculations(sp.Contract):
    def __init__(self):
        self.init()

    def division(self, a, b):
        sp.verify(b != 0, message = "DIVISION_BY_ZERO")

        return a/b

    def subtract(self, a, b):
        sp.verify(b <= a, message = "INETEGER_UNDERFLOW")

        return a - b
