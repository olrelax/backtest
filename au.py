import pandas as pd
from datetime import datetime

dtm_fmt_Y_m_d = '%Y-%m-%d'
def prn(text, color=''):
    if color == 'red':
        print('\033[31m' + text + '\033[0m')
    elif color == 'green':
        print('\033[32m' + text + '\033[0m')
    elif color == 'yellow':
        print('\033[33m' + text + '\033[0m')
    elif color == 'blue':
        print('\033[34m' + text + '\033[0m')
    elif color == 'magenta':
        print('\033[35' + text + '\033[0m')
    elif color == 'cyan':
        print('\033[36m' + text + '\033[0m')
    elif color == 'white':
        print('\033[37m' + text + '\033[0m')
    else:
        print(text)


def get_opt(df_a, quote_date,expiration,strike,t,up=True,max_delta=1,expiration_mode_search='n'):
    qd = quote_date     # datetime.strptime(quote_date,dtm_fmt_Y_m_d)
    exp = expiration    #  datetime.strptime(expiration,dtm_fmt_Y_m_d)
    df = df_a.loc[df_a['option_type'] == t].loc[df_a['quote_date'] == qd].copy()
    if not expiration_mode_search == 'e':    # not exact expiration date
        if len(df) == 0:
            return -1, None
        df_exp = df.iloc[(df['expiration'] - exp).abs().argsort()]   # exact, before and after dates
        if expiration_mode_search == 'n':     # next closest expiration date
            df_exp = df_exp.loc[df['expiration'] >= exp]    # filter dates before target
        if len(df) > 0:
            exp = df_exp['expiration'].iloc[0]
        else:
            return -2, None
    df = df.loc[df['expiration'] == exp]
    if len(df) == 0:
        return -3, None
    if up and len(df) > 1:
        df = df.iloc[(df['strike'] - strike).abs().argsort()][1:2]
    else:
        df = df.iloc[(df['strike'] - strike).abs().argsort()][0:1]
    if len(df) == 0:
        return -4, None
    ret_strike = df.iloc[0]['strike']
    if abs(ret_strike - strike) > max_delta:
        prn('Warning, strike deviation exceed limit %.2f: delta %.2f' % (max_delta,abs(ret_strike - strike)),'red')
    return 0, df.iloc[0]

'''
opts = pd.read_csv('../data/SPY_CBOE_2020_PUT.csv', index_col=0)
opts['quote_date'] = pd.to_datetime(opts['quote_date'],format='%Y-%m-%d')
opts['expiration'] = pd.to_datetime(opts['expiration'],format='%Y-%m-%d')
print(get_opt(opts,'2020-01-10','2021-09-18',325.5,'P',max_delta=1,expiration_mode_search='c'))
'''


def get_closest(df_arg, val, put_or_call):
    min_delta, premium, strike = 1000000., 0., 0
    df = df_arg.loc[df_arg['option_type'] == put_or_call]
    for index, row in df.iterrows():
        row_val = row['strike']
        delta = abs(row_val - val)
        if delta < min_delta:
            min_delta = delta
            strike = row_val
            premium = row['option_price']
    return strike, premium
