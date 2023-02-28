import pandas as pd
from datetime import datetime
import inspect
from au import read_entry,flt,scale_stock,isfloat
from plot import plot
count = 0   # 1 - single option, 2 - vertical spread
ticker = ''
start_date = ''
before_date = ''
fn = ''     # filename base for outputs
comm = 0    # commission per option
low_price_limit = 0
high_price_limit = 0
condition = 0   # global variable used for map methods
stock = ''
mf = 'mf'
capital = 0
disc_prc,hedge_usd = 0,0
dd_count,dd_raw_count,max_trades,trades = 0, 0, 0, 0
shrink_by_lower_cond,shrink_by_high_cond = 0,0
enter_time = ''
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
    df.loc[df['strike_0']>0].to_csv('../out/%s-e.csv' % fn, index=False)

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
    return df.rename(columns={'strike': 'strike_%d' % i, 'overstrike':'overstrike_%d' % i,'underlying_enter': 'under_enter_%d' % i,'under_out': 'under_out_%d' % i,
                          'enter': 'enter_%d' % i,'out': 'out_%d' % i,
                          'margin': 'margin_%d' % i,'profit': 'profit_%d' % i})

def get_sold(price):
    return 0 if price < 0.0101 else price

def add_stock_chart(out_df):
    yfn = '../data/QQQ/QQQ-yahoo.csv'
    bd = out_df['quote_date'].iloc[0]
    ed = out_df['quote_date'].iloc[-1]
    stock_df = pd.read_csv(yfn)
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    stock_df = stock_df.loc[(stock_df['Date'] <= ed) & (stock_df['Date'] >= bd)][['Date','Open']]
    stock_df = stock_df.rename(columns={'Date':'quote_date'})
    df = pd.merge(stock_df,out_df,on='quote_date',how='outer')
    return df

def make_delta_column(df_in,opt_type,params,i):

    k = (100 + params[0] * (1 if opt_type[0] == 'C' else -1)) / 100
    hedge_shift = params[1] * i * (1 if opt_type[0] == 'C' else -1)
    under_in = 'underlying_open' if enter_time == 'open' else 'underlying_bid_1545' if enter_time == '1545' else ''
    df_in['delta'] = (df_in[under_in] * k + hedge_shift - df_in['strike']).abs() * 10.0
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in

def greater_than_condition(value):
    return 1. if value > condition else 0

def less_than_condition(value):
    return 1. if value < condition else 0

def select_cols():
    head = 'quote_date,expiration,'
    body = 'strike_0,under_enter_0,enter_0,under_out_0,out_0,margin_0,profit_0,opt_sum_0,overstrike_0,'
    if count == 2:
        body = body + 'strike_1,under_enter_1,enter_1,under_out_1,out_1,margin_1,profit_1,opt_sum_1,overstrike_1,'
    cols_str = head + body + 'opt_sum,sum,opt_trade_price,raw_profit,raw_sum,lcond,hcond,stock'
    if stock in ('ltrade','strade'):
        cols_str = cols_str +',under_sum'
    return cols_str.split(',')

def scale_to_capital(df):
    if stock in ('strade', 'ltrade') and capital not in ('','per opt'):
        exit('Unable scale to capital when trade stock')
    if capital in ('','per opt'):
        return df
    elif capital in ('%','prc'):
        k = 100/hedge_usd
    elif isfloat(capital) and float(capital) > 0:
        if count < 2:
            contract_margin = 3000
        else:
            contract_margin = hedge_usd * 100
        contracts_qty = float(capital)/contract_margin
        k = 100 * contracts_qty
    else:
        exit('capital value must be in (\'\'|\'per opt\',\'%%\'|\'prc\', real number)')
    for i in range(count):
        df['opt_sum_%d' % i] = df['opt_sum_%d' % i].mul(k)
    df['opt_sum'] = df['opt_sum'].mul(k)
    df['raw_sum'] = df['raw_sum'].mul(k)
    return df



def in2exp(params, weeks,side, opt_type,i):
    global condition

    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_%s_PC_%d.csv' % (ticker,ticker,mf,weeks)
    df = pd.read_csv(opts_fn)    # ,parse_dates=['quote_date','expiration'])
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]
    df = df.loc[df['option_type'] == opt_type[0]]
    df_in = make_delta_column(df.loc[df['days_to_exp'] > 0].copy(),opt_type=opt_type,params=params,i=i)
    df_min_delta = df_in.groupby(['expiration'])['delta'].min().to_frame()
    sfx = 'open' if enter_time == 'open' else 'bid_1545' if enter_time == '1545' else ''
    df_in = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])[['quote_date', 'expiration', 'strike', 'underlying_%s' % sfx, sfx]]
    df_in = df_in.rename(columns={sfx:'enter','underlying_%s' % sfx:'underlying_enter'})
    opt_prefix = 'ask' if side[:1] == 's' else 'bid' if side[:1] == 'l' else exit("Wrong side '%s'" % side)
    under_prefix = 'bid' if side[:1] == 's' else 'ask'
    df_out = df.loc[df['quote_date'] == df['expiration']][['expiration', 'strike', 'underlying_%s_eod' % under_prefix,'%s_eod' % opt_prefix]].rename(columns={'%s_eod' % opt_prefix:'out_tmp','underlying_%s_eod' % under_prefix:'under_out'}).copy().reset_index(drop=True)
    sign = 1. if opt_type[0] == 'P' else -1.
    df_out['overstrike'] = (df_out['strike'] - df_out['under_out']) * sign
    condition = 0
    df_out['k'] = pd.Series(map(greater_than_condition,df_out['overstrike'])).to_frame()     # make out price 0.0 if not executed on expiration
    df_out['out'] = (df_out['out_tmp'] * df_out['k'])
    df_out = df_out.drop(columns=['k','out_tmp'])
    df = pd.merge(df_in, df_out, on=['expiration', 'strike']).reset_index(drop=True)
    df['margin'] = (df['enter'] - df['out']) * (1. if side[:1] == 's' else -1.)
    df['profit'] = df['margin'].sub(comm)
    df = numerate(df,i)
    return df
def backtest(types,sides,params,weeks):
    global count, low_price_limit,high_price_limit,max_trades,trades,condition,dd_raw_count,dd_count
    count = min(len(sides), len(params),len(types))
    df = None
    for i in range(count):
        df_side = in2exp(params,weeks, sides[i],types[i], i)
        df_side = df_side.sort_values(['quote_date', 'expiration'])
        df = df_side if i == 0 else pd.merge(df, df_side, on=['quote_date', 'expiration'], how='inner')
    max_trades = len(df)
    df = add_stock_chart(df)
    for i in range(count):
        df['opt_trade_price'] = df['enter_0'] if i == 0 else df['opt_trade_price'] - df['enter_%d' % i]
    df['raw_profit'] = df['profit_0']
    df['raw_sum'] = (df['raw_profit'].cumsum(axis=0)).fillna(method='ffill')
    dd_raw_count = len(df.loc[df['margin_0'] < 0])
    trades = max_trades
    if shrink_by_lower_cond > 0:
        df_max = df.loc[df['strike_0'].notnull()].sort_values('opt_trade_price')
        low_price_limit = df_max[-int(max_trades*shrink_by_lower_cond/100):]['opt_trade_price'].min()

    if low_price_limit > 0:
        condition = low_price_limit
        df['lcond'] = pd.Series(map(greater_than_condition, df['opt_trade_price'])).to_frame()
        for i in range(count):
            df['profit_%d' % i] = df['profit_%d' % i] * df['lcond']
        trades = len(df.loc[df['lcond'] > 0])
    else:
        df['lcond'] = 1

    if shrink_by_high_cond > 0:
        df_max = df.loc[df['strike_0'].notnull()].sort_values('opt_trade_price')
        high_price_limit = df_max[:int(max_trades*shrink_by_high_cond/100)]['opt_trade_price'].max()

    if high_price_limit > 0:
        condition = high_price_limit
        df['hcond'] = pd.Series(map(less_than_condition, df['opt_trade_price'])).to_frame()
        for i in range(count):
            df['profit_%d' % i] = df['profit_%d' % i] * df['hcond']
        trades = len(df.loc[(df['hcond'] > 0) & (df['lcond'] > 0)])
    else:
        df['hcond'] = 1
    dd_count = len(df.loc[(df['margin_0'] < 0) & (df['lcond'] == 1)])

    for i in range(count):
        df['opt_sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['opt_sum_%d' % i] = df['opt_sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['opt_sum'] = df['opt_sum_%d' % i] if i == 0 else df['opt_sum'] + df['opt_sum_%d' % i]
    if stock in ('ltrade','strade'):
        if stock == 'ltrade':
            df['under_profit'] = df['under_out_0'] - df['under_enter_0']
        else:
            df['under_profit'] = df['under_enter_0'] - df['under_out_0']
        df['under_sum'] = (df['under_profit'].cumsum(axis=0)).fillna(method='ffill')
        df['sum'] = df['opt_sum'] + df['under_sum']
    else:
        df['sum'] = df['opt_sum']
    df = scale_to_capital(df)
    if stock in ('plot','strade','ltrade'):
        df = scale_stock(df)
    cols = select_cols()
    return df[cols]


def main_proc():
    global before_date, start_date, fn,ticker,comm,low_price_limit,high_price_limit,stock,\
        shrink_by_high_cond,shrink_by_lower_cond,mf,capital,disc_prc,hedge_usd,enter_time
    weeks = 1
    types = read_entry('backtest','types').split(',')
    sides = read_entry('backtest','sides').split(',')
    start_date = read_entry('backtest','start_date')
    before_date = read_entry('backtest','before_date')
    enter_time = read_entry('backtest','enter_time')
    ticker = read_entry('backtest','ticker')
    disc_prc = flt(read_entry('backtest','disc_prc'))
    hedge_usd = int(read_entry('backtest','hedge_usd'))
    comm = flt(read_entry('backtest','comm'))
    low_price_limit = flt(read_entry('backtest','low_price_limit'))
    high_price_limit = flt(read_entry('backtest','high_price_limit'))
    stock = read_entry('backtest','stock',check=('plot','ltrade','strade'))
    plot_raw_result = read_entry('backtest','plot_raw_result')
    mf = read_entry('backtest','mf')
    capital = read_entry('backtest','capital')
    shrink_by_high_cond = flt(read_entry('backtest','shrink_by_high_cond'))
    shrink_by_lower_cond = flt(read_entry('backtest','shrink_by_lower_cond'))
    df = backtest(types,sides, [disc_prc,hedge_usd],weeks)
    save_test(df)
    summa = df['opt_sum'].iloc[-1] if trades > 0 else exit('No trades')
    descr_str = '{} {} {} disc {}, hedge {}'.format(ticker, types, sides, disc_prc,hedge_usd)
    limit_str = 'h_lim, %.2f, l_lim %.2f' % (high_price_limit,low_price_limit) if high_price_limit > 0 and low_price_limit > 0 else 'l_lim %.2f' % low_price_limit if low_price_limit > 0 else 'h_lim %.2f' % high_price_limit if high_price_limit > 0 else ''
    cond_str = 'shrink %d, %s' % (shrink_by_lower_cond, limit_str) if shrink_by_lower_cond > 0 else limit_str
    max_dd_val = df.loc[(df['margin_0'] < 0) & (df['lcond'] == 1)]['margin_0'].min() if dd_count > 0 else 0
    max_raw_dd_val = df.loc[df['margin_0'] < 0]['margin_0'].min() if dd_raw_count > 0 else 0
    dd_str = 'dd count %d/%d, val %.2f/%.2f' % (dd_count,dd_raw_count,-max_dd_val,-max_raw_dd_val) if dd_count > 0 or dd_raw_count > 0 else ''
    # sum_fmt = 'profit/capital $%.2f/$%.2f' % (summa,capital) if capital > 0 else 'profit %.2f%%' % summa if capital == 'prc' else 'profit %.2f' % summa
    sum_fmt = 'profit/opt %.2f' % summa if capital in ('','per opt') else 'profit %.2f%%' % summa if capital in ('%','prc') else 'profit/capital $%.2f/$%.2f' % (summa,float(capital))
    res = '%s, trades %d/%d, %s' % (sum_fmt, trades,max_trades,dd_str)
    txt = '%s, %s\n%s' % (descr_str, cond_str,res)
    if mf == 'fm':
        txt = 'Fri - Mon\n%s' % txt
    plot(df,'quote_date',txt,opt_count=count,fn=fn,stock=stock,plot_raw=plot_raw_result)



if __name__ == '__main__':
    main_proc()
