import pandas as pd
from datetime import datetime
import inspect
from au import read_entry,add_stock
from plot import plot
count = 0
single_option_col_count = 0
ticker = ''
start_date = ''
before_date = ''
fn = ''
algo = ''
comm = 0
min_price = 0
max_price = 0
min_spread_price = 0
def show(df, stop=True):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    print(df.info())
    print(df.head())
    print(df.columns.tolist())
    if stop:
        exit()

def save_test(df):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
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
    return df.rename(columns={'strike': 'strike_%d' % i, 'disc':'disc_%d' % i,'underlying_open': 'under_open_%d' % i,'under_out': 'under_out_%d' % i,
                          'open': 'open_%d' % i,'out': 'out_%d' % i,
                          'margin': 'margin_%d' % i,'profit': 'profit_%d' % i})

def get_sold(price):
    return 0 if price < 0.0101 else price

def make_delta_column(df_in,opt_type,params,i):
    k = (100 + params[0] * (1 if opt_type[0] == 'C' else -1)) / 100
    hedge_shift = params[1] * i * (1 if opt_type[0] == 'C' else -1)
    df_in['delta'] = (df_in['underlying_open'] * k + hedge_shift - df_in['strike']).abs() * 10.0
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in
def zero_or_not(disc):
    return 1. if disc > 0 else 0

def in2exp(params, weeks,side, opt_type,i):
    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_mon_fri_%s_%d.csv' % (ticker,ticker,opt_type[0],weeks)
    df = pd.read_csv(opts_fn)    # ,parse_dates=['quote_date','expiration'])
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')

    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]
    df_in = make_delta_column(df.loc[df['days_to_exp'] > 0].copy(),opt_type=opt_type,params=params,i=i)
    df_min_delta = df_in.groupby(['expiration'])['delta'].min().to_frame()
    df_in = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])[['quote_date', 'expiration', 'strike', 'underlying_open', 'open']]
    opt_prefix = 'ask' if side == 'short' else 'bid'
    under_prefix = 'bid' if side == 'short' else 'ask'
    df_out = df.loc[df['quote_date'] == df['expiration']][['expiration', 'strike', 'underlying_%s_eod' % under_prefix,'%s_eod' % opt_prefix]].rename(columns={'%s_eod' % opt_prefix:'out_tmp','underlying_%s_eod' % under_prefix:'under_out'}).copy().reset_index(drop=True)
    sign = 1. if opt_type[0] == 'P' else -1.
    df_out['disc'] = (df_out['strike'] - df_out['under_out']) * sign
    df_out['k'] = pd.Series(map(zero_or_not,df_out['disc'])).to_frame()     # make out price 0.0 if not executed on expiration
    df_out['out'] = (df_out['out_tmp'] * df_out['k'])
    df_out = df_out.drop(columns=['k','out_tmp'])
    df = pd.merge(df_in, df_out, on=['expiration', 'strike']).reset_index(drop=True)
    df['margin'] = (df['open'] - df['out']) * (1. if side == 'short' else -1.)
    df['profit'] = df['margin'].sub(comm)
    if i == 0:
        if min_price > 0:
            df = df.loc[df['open'] >= min_price]
        if max_price > 0:
            df = df.loc[df['open'] <= max_price]
    df = numerate(df,i)
    return df
def backtest(types,sides,params,weeks):
    global count, single_option_col_count
    count = min(len(sides), len(params),len(types))
    df = None
    for i in range(count):
        df_side = in2exp(params,weeks, sides[i],types[i], i)
        df_side = df_side.sort_values(['quote_date', 'expiration'])
        single_option_col_count = df_side.shape[1] - 1 if i == 0 else single_option_col_count
        df = df_side if i == 0 else pd.merge(df, df_side, on=['quote_date', 'expiration'], how='inner')
    for i in range(count):
        df['spread'] = df['margin_%d' % i] if i == 0 else df['spread'] + df['margin_%d' % i]
    if min_spread_price > 0:
        df = df.loc[df['spread'] >= min_spread_price]
    for i in range(count):
        df['sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['sum_%d' % i] = df['sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
        df['spread'] = df['margin_%d' % i] if i == 0 else df['spread'] + df['margin_%d' % i]
    return df


def backtests():
    global algo, before_date, start_date, fn,ticker,comm,min_price,max_price,min_spread_price
    weeks = 1
    draw_or_show = 'show'
    types = read_entry('backtest','types').split(',')
    sides = read_entry('backtest','sides').split(',')
    start_date = read_entry('backtest','start_date')
    before_date = read_entry('backtest','before_date')
    ticker = read_entry('backtest','ticker')
    disc_prc = float(read_entry('backtest','disc_prc'))
    hedge_usd = int(read_entry('backtest','hedge_usd'))
    comm = float(read_entry('backtest','comm'))
    min_price = float(read_entry('backtest','min_price'))
    min_spread_price = float(read_entry('backtest','min_spread_price'))
    max_price = float(read_entry('backtest','max_price'))

    df = backtest(types,sides, [disc_prc,hedge_usd],weeks)

    save_test(df)
    profit_lines_in_plot = int(df.shape[1] / single_option_col_count)
    trades = len(df)
    summa = df['sum'].iloc[-1]
    avg = summa / trades
    min_spread = df['spread'].min()
    min_max_str = '' if min_price == 0 and max_price == 0 else 'min/max price %.2f/%.2f,' % (min_price,max_price)
    txt = '{} {}, type {}, side {},param {},\ntrades {}, sum profit %.2f, avg profit %.2f,%s min_spread_price %.2f'\
        .format(ticker, algo, types, sides, [disc_prc,hedge_usd], trades) % (summa,avg,min_max_str,min_spread)
    if read_entry('backtest','join_stock') == 'y':
        df = add_stock(df)
    plot(df,'quote_date',txt,lines_count=profit_lines_in_plot,draw_or_show=draw_or_show,fn=fn)

    if draw_or_show == 'draw':
        input('pause >')


if __name__ == '__main__':
    backtests()
