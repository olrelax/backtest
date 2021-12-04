import pandas as pd
from datetime import datetime
def d2s(dtm,fmt='%Y-%m-%d'):
    return datetime.strftime(dtm,fmt)
def s2d(text,fmt='%Y-%m-%d'):
    return datetime.strptime(text,fmt)

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

def get_opt(df_a, quote_date,expiration,strike,exp_mode_search,strike_round_mode,tp='P',max_delta=1):
    qd = quote_date
    exp = expiration
    if strike_round_mode not in ('up','down','exact'):
        exit('wrong strike_round_mode')
    if exp_mode_search not in ('closest_next','closest_previous','exact'):
        exit('wrong exp_mode_search')
    df = df_a.loc[df_a['option_type'] == tp].loc[df_a['quote_date'] == qd].copy()
    if exp_mode_search == 'closest_next' or exp_mode_search == 'closest_previous':    # not exact expiration date
        if len(df) == 0:
            return -1, None
        df_exp = df.iloc[(df['expiration'] - exp).abs().argsort()]   # exact, before and after dates
        if exp_mode_search == 'closest_next':     # next closest expiration date
            df_exp = df_exp.loc[df['expiration'] >= exp]    # filter dates before target
        if len(df) > 0:
            exp = df_exp['expiration'].iloc[0]
        else:
            return -2, None
    elif not exp_mode_search == 'exact':
        exit('wrong exp_mode_search. error 005')
    df = df.loc[df['expiration'] == exp]
    if len(df) == 0:
        return -3, None
    df_bk = df.copy()
    if len(df) > 1:
        if strike_round_mode == 'up':
            df = df.iloc[(df['strike'] - strike).abs().argsort()][1:2]
        elif strike_round_mode == 'down':
            df = df.iloc[(df['strike'] - strike).abs().argsort()][0:1]
        elif strike_round_mode == 'exact':
            df = df.loc[df['strike'] == strike]
        else:
            exit('wrong strike_round mode. error 006')
    if len(df) == 0:
        s_sort = df_bk.iloc[(df_bk['strike'] - strike).abs().argsort()]
        mi = s_sort['strike'].iloc[-1]
        ma = s_sort['strike'].iloc[0]

        print(d2s(quote_date),'get_opt: looking for strike', strike,'at exp',d2s(expiration),'found,', mi,'-',ma)
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
