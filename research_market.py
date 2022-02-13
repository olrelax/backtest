import pandas as pd
from dateutil.relativedelta import *

def add_days(dt):
    return dt + relativedelta(days=7)

def spy():
    df = pd.read_csv('../data/SPY-yahoo.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['late'] = pd.Series(map(lambda x:add_days(x),df['Date']))
    df_left = df[['Date','Close','late']]
    df_right = df[['Date','Close']]
    df1 = pd.merge(df_left,df_right,left_on='late',right_on='Date')
    df1['delta'] = 100*(df1['Close_x'] - df1['Close_y'])/df1['Close_x']
    m = df1.iloc[df1['delta'].argsort()][-30:]
    print(df1['delta'].max())
    print(m)
def pattern():
    df = pd.read_csv('../data/SPY-yahoo.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df1 = df['Close'].iloc[:3]
    df2 = df['Open'].iloc[:3]

    print('df1',df1)
    print('df2',df2)
    print('dif',df1-df2)
    print(140.539993 - 141.330002)
if __name__ == '__main__':

    pattern()
