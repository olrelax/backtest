import pandas as pd
from dateutil.relativedelta import *

def merge():
    df = pd.DataFrame({'d': ['m24','m24','m1','m1','t2','t2','m8','m8','t9','t9'],
                       'e': ['m1','m1','t9','t9','t9','t9','m15','m15','m15','m15'],
                       's':[100,101,111,112,111,112,131,132,131,132]})
    df_exp = df[['e']].drop_duplicates(subset='e')
    print(df_exp)
    df = df_exp.merge(df,left_on='e',right_on='d')
    print(df)

def locd():
    df_in2exp = pd.DataFrame({'date': [1,2,3],
                       'exp': [3,4,5],
                       's':[100,101,102]})

    df_all = pd.DataFrame({'date': [1,2,3,2,3,4,3,4,5],
                            'exp': [3,3,3,4,4,4,5,5,5],
                              's':[100,101,101,102,102,102,103,103,103]})
    print(df_all)

def dic():
    d = {'type': ['C','C','C'], 'side': ['S', 'S', 'L']}
    print(type(d))
    a = [1,2]
    print(type(a))
    b = (1,2)
    print(type(b))
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

if __name__ == '__main__':
    locd()
