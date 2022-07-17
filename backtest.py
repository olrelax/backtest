import pandas as pd
from datetime import datetime
import inspect
from plot import plot
count = 0
single_pos_len = 0
ticker = ''
start_date = ''
before_date = ''
fn = ''
algo = ''
strike_loss_limit = -100
premium_limit = 0
comm = 0
def show(df, stop=True):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    print(df.info())
    print(df.head())
    print(df.columns.tolist())
    if stop:
        exit()

def save_test(df, types, sides, params,exp_weekday):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn, 'w')
    print('type {},sides{},params{}, str_loss_lim {},{}'.format(types, sides, params, strike_loss_limit,exp_weekday), file=ini)
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

def numerate(df,i):
    return df.rename(columns={'strike': 'strike_%d' % i, 'underlying_open': 'under_open_%d' % i,
                          'open': 'open_%d' % i,'out': 'out_%d' % i,
                          'margin': 'margin_%d' % i,'profit': 'profit_%d' % i})

def get_sold(price):
    return 0 if price < 0.0101 else price

def make_delta_column(df_in,opt_type,disc):
    k = (100 + disc * (1 if opt_type == 'Call' else -1)) / 100
    df_in['delta'] = (df_in['underlying_open'] * k - df_in['strike']).abs() * 10.0
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in
def zero_or_not(diff):
    return 1. if diff > 0 else 0

def in2exp(param, weeks,side, i):

    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_mon_fri_%d.csv' % (ticker,ticker,weeks)
    df = pd.read_csv(opts_fn,parse_dates=['quote_date','expiration'])
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]
    df_in = make_delta_column(df.loc[df['days_to_exp'] > 0].copy(),opt_type='P',disc=param)
    df_min_delta = df_in.groupby(['expiration'])['delta'].min().to_frame()
    df_in = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])[['quote_date', 'expiration', 'strike', 'underlying_open', 'open']]
    prefix = 'ask' if side == 'short' else 'bid'
    df_out = df.loc[df['quote_date'] == df['expiration']][['expiration', 'strike', 'underlying_close','%s_eod' % prefix]].rename(columns={'%s_eod' % prefix:'out_tmp','underlying_close':'under_out'}).copy().reset_index(drop=True)
    df_out['diff'] = df_out['strike'] - df_out['under_out']
    df_out['k'] = pd.Series(map(zero_or_not,df_out['diff'])).to_frame()
    df_out['out'] = df_out['out_tmp'] * df_out['k']
    # save(df_out,None,True)
    df = pd.merge(df_in, df_out, on=['expiration', 'strike']).reset_index(drop=True)
    # df['margin'] = (df['open'] - pd.Series(map(get_sold, df['out']))) * (1. if side == 'short' else -1.)
    df['margin'] = (df['open'] - df['out']) * (1. if side == 'short' else -1.)
    df['profit'] = df['margin'].sub(comm)
    df = numerate(df,i)
    df['exit_date'] = df['expiration']
    cols = df.columns.tolist()
    cols.insert(2, 'exit_date')
    cols.pop(-1)
    df['enter_date'] = df['quote_date']
    cols.insert(2, 'enter_date')
    df = df[cols]
    return df
def backtest(sides,params,weeks):
    global count, single_pos_len
    count = min(len(sides), len(params))
    df = None
    for i in range(count):
        df_side = in2exp(params[i],weeks, sides[i], i)
        df_side = df_side.sort_values(['exit_date', 'enter_date'])
        single_pos_len = df_side.shape[1] - 1 if i == 0 else single_pos_len
        df = df_side if i == 0 else pd.merge(df, df_side, on=['exit_date', 'enter_date'], how='outer')
    df = df.rename(columns={'quote_date_x':'quote_date','expiration_x':'expiration'})
    df = df.sort_values(['exit_date', 'enter_date'])

    for i in range(count):
        df['sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['sum_%d' % i] = df['sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df


def backtests():
    global algo, before_date, start_date, fn,strike_loss_limit,premium_limit,ticker,comm
    ticker = 'QQQ'
    types = ['Put', 'Put']
    sides = ['short','long']
    params = [23,]
    weeks = 4
    strike_loss_limit = None  # in USD if > 1 else in %
    start_date = '2020-01-01'
    before_date = '2023-01-01'
    premium_limit = None
    draw_or_show = 'show'
    comm = 0.01

    df = backtest(sides, params,weeks)

    save_test(df, types, sides, params,weeks)
    lines_in_plot = int(df.shape[1] / single_pos_len)
    trades = len(df)
    summa = df['sum'].iloc[-1]
    avg = summa / trades
    txt = '{} {}, type {}, side {},param {},\ntrades {}, sum %.2f, avg %.2f'\
        .format(ticker, algo, types, sides, params, trades) % (summa,avg)
    plot(df,txt,lines_count=lines_in_plot,draw_or_show=draw_or_show,fn=fn)
    if draw_or_show == 'draw':
        input('pause >')


if __name__ == '__main__':
    backtests()
