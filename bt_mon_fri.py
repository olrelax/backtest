import pandas as pd
from datetime import datetime
import inspect
from plot import plot
single_pos_len = 0
ticker = ''
start_date = ''
before_date = ''
fn = ''
algo = ''
strike_loss_limit = -100
premium_limit = 0
enter_time = '1545'

def show(df, stop=True, ):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    print(df.head())
    print(df.columns.tolist())
    if stop:
        exit()

def save_test(df, types, sides, params):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn, 'w')
    print('type {},sides{},params{}, str_loss_lim {}'.format(types, sides, params, strike_loss_limit), file=ini)
    ini.close()
    # noinspection PyTypeChecker
    df.to_csv('../out/e-%s.csv' % fn, index=False)

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
    if stop:
        exit()


def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def get_sold(price):
    return 0 if price < 0.0101 else price
def make_delta_column(df_in,param):
    if algo == 'dist':
        dist = param
        df_in['delta'] = (df_in['underlying_ask_1545'].sub(dist).sub(df_in['strike']).abs() * 10.0)
    elif algo == 'disc':
        disc = param
        k = (100 - disc) / 100
        df_in['delta'] = (df_in['underlying_ask_1545'] * k - df_in['strike']).abs() * 10.0
    elif algo == 'price':
        df_in['delta'] = df_in['bid_1545'].sub(param).abs() * 100
    else:
        exit('algo?')
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in
def numerate(df,i):
    df = df.rename(columns={'strike': 'strike_%d' % i, 'underlying_bid_1545': 'under_bid_in_%d' % i,
                          'underlying_ask_1545': 'under_ask_in_%d' % i,'high':'high_%d' % i,
                          'bid_1545': 'bid_in_%d' % i, 'ask_1545': 'ask_in_%d' % i,
                          'underlying_bid_eod': 'under_bid_out_%d' % i,
                          'underlying_ask_eod': 'under_ask_out_%d' % i, 'bid_eod': 'bid_out_%d' % i,
                          'ask_eod': 'ask_out_%d' % i,
                          'margin': 'margin_%d' % i})
    return df

def get_in2exp_mf(param, side, i):
    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_mon_fri_P.csv' % (ticker,ticker)
    df = pd.read_csv(opts_fn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]

    df_in = df.loc[df['days_to_exp'] > 0].copy()
    df_in = make_delta_column(df_in,param)
    min_delta_series = df_in.groupby(['expiration'])['delta'].min()
    df_min_delta = min_delta_series.to_frame()
    df_in_filtered = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])
    df_in = df_in_filtered[['quote_date', 'expiration', 'strike', 'underlying_bid_1545', 'underlying_ask_1545', 'bid_1545', 'ask_1545','high']]


    df_out = df.loc[df['quote_date'] == df['expiration']]
    df_out = df_out[['expiration', 'strike', 'underlying_bid_1545', 'underlying_ask_1545', 'bid_1545', 'ask_1545',
                   'underlying_bid_eod', 'underlying_ask_eod', 'bid_eod', 'ask_eod']]
    df_out = df_out.rename(
        columns={'underlying_bid_1545': 'under_bid_1545_out_%d' % i, 'underlying_ask_1545': 'under_ask_1545_out_%d' % i,
                 'high':'high_%d' % i,'bid_1545': 'bid_1545_out_%d' % i, 'ask_1545': 'ask_1545_out_%d' % i})
    df = pd.merge(df_in, df_out, on=['expiration', 'strike']).reset_index(drop=True)
    enter_short = 'bid_1545' if enter_time == '1545' else 'high'
    enter_long = 'ask_1545' if enter_time == '1545' else 'high'
    if side == 'S':
        df['margin'] = (df[enter_short] - pd.Series(map(get_sold, df['ask_eod'])))
    else:
        df['margin'] = (pd.Series(map(get_sold, df['bid_eod'])) - df[enter_long])
    df = numerate(df,i)
    df['exit_date'] = df['expiration']
    cols = df.columns.tolist()
    cols.insert(2, 'exit_date')
    cols.pop(-1)
    df['enter_date'] = df['quote_date']
    cols.insert(2, 'enter_date')
    df = df[cols]
    return df
def bt_mon_fri(sides,params):
    global single_pos_len
    count = min(len(sides), len(params))
    df = None
    for i in range(count):
        df_side = get_in2exp_mf(params[i], sides[i], i)
        df_side = df_side.sort_values(['exit_date', 'enter_date'])
        single_pos_len = df_side.shape[1] - 1 if i == 0 else single_pos_len
        df = df_side if i == 0 else pd.merge(df, df_side, on=['exit_date', 'enter_date'], how='outer')
    df = df.rename(columns={'quote_date_x':'quote_date','expiration_x':'expiration'})
    df = df.sort_values(['exit_date', 'enter_date'])

    for i in range(count):
        df['sum_%d' % i] = df['margin_%d' % i].cumsum(axis=0)
        df['sum_%d' % i] = df['sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df


def backtests():
    global algo, before_date, start_date, fn,strike_loss_limit,premium_limit,ticker,enter_time
    ticker = 'QQQ'
    types = ['P', 'P']
    sides = ['S','L']
    params = [9,12]
    algo = 'disc'
    enter_time = '154'
    strike_loss_limit = None  # in USD if > 1 else in %
    start_date = '2022-01-01'
    before_date = '2023-01-01'
    premium_limit = None
    draw_or_show = 'show'
    df = bt_mon_fri(sides, params)

    save_test(df, types, sides, params)
    lines_in_plot = int(df.shape[1] / single_pos_len)
    trades = len(df)
    comm = 0.0105
    txt = '{}, type {}, side {},param {},\n str_loss_lim {}, premium_lim {}\ntrades {}, comm {}'\
        .format(algo, types, sides, params, strike_loss_limit,premium_limit,trades,comm)
    plot(df,txt,lines_count=lines_in_plot,draw_or_show=draw_or_show,fn=fn)
    if draw_or_show == 'draw':
        input('pause >')


if __name__ == '__main__':
    backtests()
