import pandas as pd
from dateutil.relativedelta import *
from au import s2d
import numpy as np
import csv


def isin():
    df1 = pd.DataFrame({'col1':[1,2,3,4],'col2':['a1','b1','c1','d1']})
    df2 = pd.DataFrame({'col1':[11,2,3,44],'col2':['aa2','b2','c2','dd2']})
    df1_in_d2 = df1.loc[df1['col1'].isin(df2['col1'])]
    print(df1_in_d2)
if __name__ == '__main__':
    print('\u534D')
