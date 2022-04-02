import pandas as pd
from dateutil.relativedelta import *
from au import s2d
import numpy as np
import csv


def fun(a):
    return 2 * a


class Cl:
    a = 0

    def center(self):
        self.a = 3


def locd():
    c = Cl()
    print(c.center)


if __name__ == '__main__':
    locd()
