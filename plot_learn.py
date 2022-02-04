import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
# plt.ion()
START_DATE = dt.datetime(2019,8,1,0,0,0)
END_DATE = dt.datetime(2019,8,20,0,0,0)
df = pd.DataFrame({'date': pd.date_range(start=START_DATE, end=END_DATE, freq='1D')})

def make_df(y):
    df['y'] = pd.Series(y[:,0])
    df.set_index('date')
    return df
def ex1():
    for i in range(50):
        y = np.random.random([20,1])
        plt.plot(y)
        plt.draw()
        plt.pause(0.0001)
        plt.clf()
def ex2():
    for i in range(50):
        y = np.random.random([20,1])
        dfp = make_df(y)
        plt.plot(dfp['date'],dfp['y'])
        plt.xticks(rotation=30)
        plt.draw()
        plt.pause(0.0001)
        input('>')
        plt.clf()
def ex3():
    y = np.random.random([20, 1])
    dfp = make_df(y)
    plt.plot(dfp['date'], dfp['y'])
    plt.xticks(rotation=30)
    #plt.draw()
    #plt.pause(0.0001)
    #plt.clf()
    plt.show()

ex2()
