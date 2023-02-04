import pandas as pd
from datetime import datetime
import inspect
from au import read_entry,flt,scale_stock
from plot import plot
count = 0
single_option_col_count = 0
ticker = ''
start_date = ''
before_date = ''
fn = ''
comm = 0
max_price = 0
low_price_limit = 0
condition = 0

stock = ''
dd_count,dd_raw_count,max_trades,trades = 0, 0, 0, 0
shrink_to = 0
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
    df.to_csv('../out/%s-e.csv' % fn, index=False)

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
    return df.rename(columns={'strike': 'strike_%d' % i, 'overstrike':'overstrike_%d' % i,'underlying_open': 'under_open_%d' % i,'under_out': 'under_out_%d' % i,
                          'open': 'open_%d' % i,'out': 'out_%d' % i,
                          'margin': 'margin_%d' % i,'profit': 'profit_%d' % i})

def get_sold(price):
    return 0 if price < 0.0101 else price


def add_stock_chart(out_df):
    yfn = '../data/QQQ/QQQ-yahoo.csv'
    bd = out_df['quote_date'].iloc[0]
    ed = out_df['quote_date'].iloc[-1]
    stock_df = pd.read_csv(yfn)
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    stock_df = stock_df.loc[(stock_df['Date'] <= ed) & (stock_df['Date'] >= bd)]
    stock_df = stock_df.rename(columns={'Date':'quote_date'})
    df = pd.merge(stock_df,out_df,on='quote_date',how='outer')
#    for i in range(count):
#        df['opt_sum_%d' % i] = df['opt_sum_%d' % i].fillna(method='ffill')
#    df['opt_sum'] = df['opt_sum'].fillna(method='ffill')
#    if trade_stock in ('s','l'):
#        df['under_sum'] = df['under_sum'].fillna(method='ffill')
#    df['sum'] = df['sum'].fillna(method='ffill')
    return df

def make_delta_column(df_in,opt_type,params,i):
    k = (100 + params[0] * (1 if opt_type[0] == 'C' else -1)) / 100
    hedge_shift = params[1] * i * (1 if opt_type[0] == 'C' else -1)
    df_in['delta'] = (df_in['underlying_open'] * k + hedge_shift - df_in['strike']).abs() * 10.0
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in

def greater_than_condition(value):
    return 1. if value > condition else 0

def in2exp(params, weeks,side, opt_type,i):
    global condition
    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_mon_fri_PC_%d.csv' % (ticker,ticker,weeks)
    df = pd.read_csv(opts_fn)    # ,parse_dates=['quote_date','expiration'])
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]
    df = df.loc[df['option_type'] == opt_type[0]]
    df_in = make_delta_column(df.loc[df['days_to_exp'] > 0].copy(),opt_type=opt_type,params=params,i=i)
    df_min_delta = df_in.groupby(['expiration'])['delta'].min().to_frame()
    df_in = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])[['quote_date', 'expiration', 'strike', 'underlying_open', 'open']]
    opt_prefix = 'ask' if side == 'short' else 'bid' if side == 'long' else exit("Wrong side '%s'" % side)
    under_prefix = 'bid' if side == 'short' else 'ask'
    df_out = df.loc[df['quote_date'] == df['expiration']][['expiration', 'strike', 'underlying_%s_eod' % under_prefix,'%s_eod' % opt_prefix]].rename(columns={'%s_eod' % opt_prefix:'out_tmp','underlying_%s_eod' % under_prefix:'under_out'}).copy().reset_index(drop=True)
    sign = 1. if opt_type[0] == 'P' else -1.
    df_out['overstrike'] = (df_out['strike'] - df_out['under_out']) * sign
    condition = 0
    df_out['k'] = pd.Series(map(greater_than_condition,df_out['overstrike'])).to_frame()     # make out price 0.0 if not executed on expiration
    df_out['out'] = (df_out['out_tmp'] * df_out['k'])
    df_out = df_out.drop(columns=['k','out_tmp'])
    df = pd.merge(df_in, df_out, on=['expiration', 'strike']).reset_index(drop=True)
    df['margin'] = (df['open'] - df['out']) * (1. if side == 'short' else -1.)
    df['profit'] = df['margin'].sub(comm)
    df = numerate(df,i)
    return df
def backtest(types,sides,params,weeks):
    global count, low_price_limit,max_trades,trades,condition,dd_raw_count,dd_count
    count = min(len(sides), len(params),len(types))
    df = None
    for i in range(count):
        df_side = in2exp(params,weeks, sides[i],types[i], i)
        df_side = df_side.sort_values(['quote_date', 'expiration'])
        df = df_side if i == 0 else pd.merge(df, df_side, on=['quote_date', 'expiration'], how='inner')
    max_trades = len(df)
    df = add_stock_chart(df)
    for i in range(count):
        df['opt_trade_price'] = df['open_0'] if i == 0 else df['opt_trade_price'] - df['open_%d' % i]
    df['raw_profit'] = df['profit_0']
    df['raw_sum'] = (df['raw_profit'].cumsum(axis=0)).fillna(method='ffill')
    dd_raw_count = len(df.loc[df['margin_0'] < 0])
    if shrink_to > 0:
        df_max = df.loc[df['strike_0'].notnull()].sort_values('opt_trade_price')
        low_price_limit = df_max[-int(max_trades*shrink_to/100):]['opt_trade_price'].min()

    if low_price_limit > 0:
        condition = low_price_limit
        df['cond'] = pd.Series(map(greater_than_condition, df['opt_trade_price'])).to_frame()
        for i in range(count):
            df['profit_%d' % i] = df['profit_%d' % i] * df['cond']
        trades = len(df.loc[df['cond'] > 0])
    else:
        trades = max_trades
    dd_count = len(df.loc[(df['margin_0'] < 0) & (df['cond'] == 1)])

    for i in range(count):
        df['opt_sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['opt_sum_%d' % i] = df['opt_sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['opt_sum'] = df['opt_sum_%d' % i] if i == 0 else df['opt_sum'] + df['opt_sum_%d' % i]
        df['opt_trade_price'] = df['margin_%d' % i] if i == 0 else df['opt_trade_price'] + df['margin_%d' % i]
    if stock in ('ltrade','strade'):
        if stock == 'ltrade':
            df['under_profit'] = df['under_out_0'] - df['under_open_0']
        else:
            df['under_profit'] = df['under_open_0'] - df['under_out_0']
        df['under_sum'] = df['under_profit'].cumsum(axis=0)
        df['sum'] = df['opt_sum'] + df['under_sum']
    else:
        df['sum'] = df['opt_sum']
    if stock in ('plot','strade','ltrade'):
        df = scale_stock(df)
    return df


def main_proc():
    global before_date, start_date, fn,ticker,comm,max_price,low_price_limit,stock,shrink_to
    weeks = 1
    types = read_entry('backtest','types').split(',')
    sides = read_entry('backtest','sides').split(',')
    start_date = read_entry('backtest','start_date')
    before_date = read_entry('backtest','before_date')
    ticker = read_entry('backtest','ticker')
    disc_prc = flt(read_entry('backtest','disc_prc'))
    hedge_usd = int(read_entry('backtest','hedge_usd'))
    comm = flt(read_entry('backtest','comm'))
    low_price_limit = flt(read_entry('backtest','low_price_limit'))
    high_price_limit = flt(read_entry('backtest','high_price_limit'))
    stock = read_entry('backtest','stock')
    shrink_to = flt(read_entry('backtest','shrink_to_prc'))
    df = backtest(types,sides, [disc_prc,hedge_usd],weeks)
    save_test(df)
    summa = df['opt_sum'].iloc[-1] if trades > 0 else exit('No trades')
    descr_str = '{} {} {} disc {}, hedge {}'.format(ticker, types, sides, disc_prc,hedge_usd)
    limit_str = 'h_lim, %.2f, l_lim %.2f' % (high_price_limit,low_price_limit) if high_price_limit > 0 and low_price_limit > 0 else 'l_lim %.2f' % low_price_limit if low_price_limit > 0 else 'h_lim %.2f' % high_price_limit if high_price_limit > 0 else ''
    cond_str = 'shrink %d, %s' % (shrink_to, limit_str) if shrink_to > 0 else limit_str
    max_dd_val = df.loc[(df['margin_0'] < 0) & (df['cond'] == 1)]['margin_0'].min() if dd_count > 0 else 0
    max_raw_dd_val = df.loc[df['margin_0'] < 0]['margin_0'].min() if dd_raw_count > 0 else 0
    dd_str = 'dd count %d/%d, val %.2f/%.2f' % (dd_count,dd_raw_count,-max_dd_val,-max_raw_dd_val) if dd_count > 0 or dd_raw_count > 0 else ''
    res = 'sum %.2f, tr %d/%d, %s' % (summa, trades,max_trades,dd_str)
    txt = '%s, %s\n%s' % (descr_str, cond_str,res)
    plot(df,'quote_date',txt,opt_count=count,fn=fn,stock=stock)



if __name__ == '__main__':
    main_proc()
