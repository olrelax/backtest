import pandas as pd
from dateutil.relativedelta import *
from au import s2d
import numpy as np
import csv

def fun(a):
    return 2*a

def locd():

    df = pd.DataFrame({'date': [1,2,3,2,3,4,3,4,5],
                       'exp': [3,3,3,4,4,4,5,5,5],
                       's':[100,101,101,102,102,102,103,103,103]})
    mp = map(fun, df.date)
    df['m'] = pd.Series(mp)
    print(df)




if __name__ == '__main__':
    locd()
