import pandas as pd
from dateutil.relativedelta import *
from au import s2d
def merge():
    dfl = pd.DataFrame({'d': ['d1','d2','d3'],
                       'e': ['e1','e2','e3'],
                       's':[100,101,111]})
    dfr = pd.DataFrame({'d': ['d1','d2','d4'],
                       'e': ['e1','e2','e4'],
                       's':[110,111,121]})
    df = pd.merge(dfl,dfr,on=['d','e'],how='outer')
    print(df)

def locd():
    df_in2exp = pd.DataFrame({'date': [1,2,3],
                       'exp': [3,4,5],
                       's':[100,101,102]})

    df_all = pd.DataFrame({'date': [1,2,3,2,3,4,3,4,5],
                           'exp': [3,3,3,4,4,4,5,5,5],
                           's':[100,101,101,102,102,102,103,103,103]})
    print(df_all)

def locs():
    df = pd.DataFrame({'x': [1,2,3,2],
                       'a': ['aabb','bbb','ccc','sdf'],
                       'b':[100,101,101,102]})
    print(df.loc[df.a.str.contains('aa')])

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

def tax():

    df = pd.date_range(start='1/1/2021',end='12/31/2021').to_frame(False,name='date')
    kurs_path = "/Users/oleg/Dropbox/Business/BANKS-BROKERS-TAX/USA-EU/CITI/NY/Statements/kurs_2021.csv"
    s49_path = "/Users/oleg/Dropbox/Business/BANKS-BROKERS-TAX/USA-EU/CITI/NY/Statements/Saving_0049/SAV_0049_2021.csv"
    s88_path = "/Users/oleg/Dropbox/Business/BANKS-BROKERS-TAX/USA-EU/CITI/NY/Statements/Saving_8809/SAV_8809_2021.csv"
    kurs = pd.read_csv(kurs_path)
    kurs['date'] = pd.to_datetime(kurs['date'], format='%d.%m.%Y')
    kurs = pd.merge(df,kurs,on='date',how='outer')
    kurs['USD'] = kurs['USD'].fillna(method='ffill')
    kurs = kurs.drop(columns={'EUR','GBP'})
    kurs = kurs.rename(columns={'date':'Date'})

    # print(df.head(12))
    s49 = pd.read_csv(s49_path,index_col=False).drop(columns='Status')
    s88 = pd.read_csv(s88_path,index_col=False).drop(columns='Status')
    s49['Date'] = pd.to_datetime(s49['Date'], format='%m-%d-%Y')
    s88['Date'] = pd.to_datetime(s88['Date'], format='%m-%d-%Y')
    bank = s49.append(s88,ignore_index=True)
    bank = pd.merge(bank,kurs,on='Date').sort_values('Date')
    bank['Debit'] = bank['Debit'].fillna(0)
    bank['Credit'] = bank['Credit'].fillna(0)
    bank['DEB_R'] = bank.Debit.mul(bank.USD)
    bank['CRED_R'] = bank.Credit.mul(bank.USD)
    bank = bank.loc[(bank['Description'] == 'INTEREST PAYMENT ') | (bank['Description'] == 'Interest Payment ') | (bank['Description'] == 'Federal Withholding Tax ') | (bank['Description'] == 'FEDERAL WITHHOLDING TAX ')]
    sum_deb = bank.DEB_R.sum()
    sum_cred = bank.CRED_R.sum()

    # noinspection PyTypeChecker
    total = pd.Series({'Date':s2d('2021-12-31'),'Description':'Total','DEB_R':round(sum_deb,2),'CRED_R':round(sum_cred,2)})
    bank = bank.append(total,ignore_index=True)
    bank.to_csv('../out/bank.csv',index=False)
if __name__ == '__main__':
    merge()
