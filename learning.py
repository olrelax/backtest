import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import au
from au import s2d,fl,d2s,add_days
from inspect import currentframe, getframeinfo
import matplotlib.pyplot as plt
from os import system
from position import Position
from datetime import datetime
import time
import sqlitetocsv as sql
import globalvars as gv

from inspect import currentframe, getframeinfo
from au import fl


def learn():

    w = gv.ini('trade_day_of_week')
    print(type(w))


if __name__ == '__main__':
    learn()
