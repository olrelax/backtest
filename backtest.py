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
low_spread_price_limit = 0
high_opt_price_limit = 0
condition = 0   # global variable used for map methods
stock = ''
mf = 'mf'
capital = 0
dd_count,dd_raw_count,max_trades,trades = 0, 0, 0, 0
shrink_by_lower_cond,shrink_by_high_cond = 0,0
enter_time = ''
hedge_usd,disc_prc = 0,0
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
    return df.rename(columns={'strike': 'strike_%d' % i, 'overstrike':'overstrike_%d' % i,'under_enter': 'under_enter_%d' % i,'under_out': 'under_out_%d' % i,
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

def greater_than_condition(value):
    return 1. if value > condition else 0

def less_than_condition(value):
    return 1. if value < condition else 0

def select_cols():
    head = 'quote_date,expiration,'
    body = 'strike_0,under_enter_0,enter_0,under_out_0,out_0,margin_0,profit_0,opt_sum_0,overstrike_0,'
    if count == 2:
        body = body + 'strike_1,under_enter_1,enter_1,under_out_1,out_1,margin_1,profit_1,opt_sum_1,overstrike_1,'
    cols_str = head + body + 'opt_sum,sum,spread_price,raw_profit,raw_sum,lcond,hcond'
    if stock in ('ltrade','strade'):
        cols_str = cols_str +',stock,under_sum'
    if stock == 'plot':
        cols_str = cols_str + ',stock'
    return cols_str.split(',')

def scale_to_capital(df):
    if stock in ('strade', 'ltrade') and capital not in ('','per opt'):
        return exit('Unable scale to capital when trade stock')
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
        return exit('capital value must be in (\'\'|\'per opt\',\'%%\'|\'prc\', real number)')
    for i in range(count):
        df['opt_sum_%d' % i] = df['opt_sum_%d' % i].mul(k)
    df['opt_sum'] = df['opt_sum'].mul(k)
    df['raw_sum'] = df['raw_sum'].mul(k)
    return df


algo_names = ['', '']
algo_values = [0, 0]
def decode_algo(algo_str):
    global algo_names,algo_values
    algo = algo_str.split(',')
    for i in range(count):
        algo_i = algo[i].strip()
        split = ' ' if ' ' in algo_i else '='
        algo_names[i] = algo_i.split(split)[0].strip()
        algo_values[i] = algo_i.split(split)[1].strip()
        if algo_names[i] in ('op','otm_prc'):
            algo_names[i] = 'otm_prc'
        elif algo_names[i] in ('ou','otm_usd'):
            algo_names[i] = 'otm_usd'
        elif algo_names[i] in ('hu','hedge_usd'):
            algo_names[i] = 'hedge_usd'
        elif algo_names[i] in ('fp', 'fixed_price','fix_price'):
            algo_names[i] = 'fixed_price'
        else:
            exit('Unknown algo_name <%s>. Choose one:\nop|otm_prc, ou|otm_usd, hu|hedge_usd,fp|fix[ed]_price' % algo_names[i])

k=0
def make_delta_column(df_in,opt_type,i):
    global hedge_usd,disc_prc,k
    if i%2 == 0:
        hedge_usd = 35
        if algo_names[i] == 'otm_prc':
            prc = float(algo_values[i])
            disc_prc = prc
            k = (100. + prc * (1 if opt_type[0] == 'Call' else -1.)) / 100.
            if i == 0:
                df_in['delta'] = (df_in['under_enter'] * k - df_in['strike']).abs() * 10.0
                df_in['delta'] = df_in['delta'].astype(int)
        elif algo_names[i] == 'fixed_price':
            price = float(algo_values[i])
            df_in['delta'] = ((df_in['enter'].sub(price)).abs()*100.0).astype(int)
        else:
            return exit('Wrong algo %d <%s>' % (i, algo_names[i]))
    if i%2 == 1:
        if algo_names[i] == 'hedge_usd':
            usd = int(algo_values[i])
            hedge_shift = usd * i * (1 if opt_type[0] == 'Call' else -1)
            hedge_usd = abs(hedge_shift)
            df_in['delta'] = (df_in['under_enter'] * k + hedge_shift - df_in['strike']).abs() * 10.0
            df_in['delta'] = df_in['delta'].astype(int)
        elif algo_names[i] == 'otm_prc':
            hedge_usd = 0
            prc = float(algo_values[i])
            k = (100. + prc * (1 if opt_type[0] == 'Call' else -1.)) / 100.
            df_in['delta'] = (df_in['under_enter'] * k - df_in['strike']).abs() * 10.0
            df_in['delta'] = df_in['delta'].astype(int)
        else:
            return exit('Wrong algo %d <%s>' % (i,algo_names[i]))
    return df_in


def in2exp(side, opt_type,i):
    global condition

    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/%s/%s_%s_PC_1.csv' % (ticker,ticker,mf)
    df = pd.read_csv(opts_fn)    # ,parse_dates=['quote_date','expiration'])
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]
    df = df.loc[df['option_type'] == opt_type[0]]
    if enter_time == 'open':
        enter_price = 'open'
        under_enter_price = 'underlying_open'
    elif enter_time == '1545':
        enter_price = 'bid_1545'
        if side[:1] == 's':
            if opt_type == 'Put':
                under_enter_price = 'underlying_bid_1545'
            else:
                under_enter_price = 'underlying_ask_1545'
        else:   # side[:1] == 'l':
            if opt_type == 'Put':
                under_enter_price = 'underlying_ask_1545'
            else:
                under_enter_price = 'underlying_bid_1545'
    else:
        enter_price = 'err'
        under_enter_price = 'err'
        exit('Wrong enter time %s' % enter_time)

    df = df.rename(columns={enter_price:'enter',under_enter_price:'under_enter','close':'out_tmp','underlying_close':'under_out'})
    df = df.loc[((df['quote_date'] < df['expiration']) & (df['enter'] > 0.01)) | (df['quote_date'] == df['expiration'])]
    df = df[['quote_date','expiration','under_enter','strike','enter','under_out','out_tmp','days_to_exp']]
    df_in = make_delta_column(df.loc[df['days_to_exp'] > 0].copy(),opt_type=opt_type,i=i)
    df_min_delta = df_in.groupby(['expiration'])['delta'].min().to_frame()
    df_in = pd.merge(df_min_delta, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration'])
    df_in = df_in.drop_duplicates(subset=['quote_date', 'expiration'])
    df_in = df_in[['expiration', 'delta', 'quote_date', 'under_enter', 'strike', 'enter']]
    df_out = df.loc[df['quote_date'] == df['expiration']][['expiration', 'strike', 'under_out','out_tmp']].copy().reset_index(drop=True)
    sign = 1. if opt_type == 'Put' else -1 if opt_type == 'Call' else exit('Wrong opt_type {}'.format(opt_type))
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
def backtest(types,sides,algo_str):
    global count, low_spread_price_limit,high_opt_price_limit,max_trades,trades,condition,dd_raw_count,dd_count
    count = min(len(sides), len(types),len(algo_str.split(',')))
    df = None
    decode_algo(algo_str)
    for i in range(count):
        df_side = in2exp(sides[i],types[i],i)
        df_side = df_side.sort_values(['quote_date', 'expiration'])
        df = df_side if i == 0 else pd.merge(df, df_side, on=['quote_date', 'expiration'], how='inner')
    max_trades = len(df)
    df = add_stock_chart(df)
    for i in range(count):
        df['spread_price'] = df['enter_0'] if i == 0 else df['spread_price'] - df['enter_%d' % i]
    df['raw_profit'] = df['profit_0']
    df['raw_sum'] = (df['raw_profit'].cumsum(axis=0)).fillna(method='ffill')
    dd_raw_count = len(df.loc[df['margin_0'] < 0])
    trades = max_trades
    if shrink_by_lower_cond > 0:
        df_max = df.loc[df['strike_0'].notnull()].sort_values('spread_price')
        low_spread_price_limit = df_max[-int(max_trades*shrink_by_lower_cond/100):]['spread_price'].min()

    if low_spread_price_limit > 0:
        condition = low_spread_price_limit
        df['lcond'] = pd.Series(map(greater_than_condition, df['spread_price'])).to_frame()
        for i in range(count):
            df['profit_%d' % i] = df['profit_%d' % i] * df['lcond']
        trades = len(df.loc[df['lcond'] > 0])
    else:
        df['lcond'] = 1

    if shrink_by_high_cond > 0:
        df_max = df.loc[df['strike_0'].notnull()].sort_values('spread_price')
        high_opt_price_limit = df_max[:int(max_trades*shrink_by_high_cond/100)]['spread_price'].max()

    if high_opt_price_limit > 0:
        condition = high_opt_price_limit
        df['hcond'] = pd.Series(map(less_than_condition, df['spread_price'])).to_frame()
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
def read_types(a_types):
    types = a_types.split(',')
    cnt = len(types)
    for i in range(cnt):
        if types[i] not in ('Put','Call'):
            exit('Wrong type %s' % types[i])
    return types

def main_proc():
    global before_date, start_date, fn,ticker,comm,low_spread_price_limit,high_opt_price_limit,stock,\
        shrink_by_high_cond,shrink_by_lower_cond,mf,capital,disc_prc,hedge_usd,enter_time
    types = read_types(read_entry('backtest','types'))
    sides = read_entry('backtest','sides').split(',')
    algo_str = read_entry('backtest','sides_algo')
    start_date = read_entry('backtest','start_date')
    before_date = read_entry('backtest','before_date')
    enter_time = read_entry('backtest','enter_time')
    ticker = read_entry('backtest','ticker')
    comm = flt(read_entry('backtest','comm'))
    low_spread_price_limit = flt(read_entry('backtest','low_spread_price_limit'))
    high_opt_price_limit = flt(read_entry('backtest','high_opt_price_limit'))
    stock = read_entry('backtest','stock',check=('plot','ltrade','strade'))
    plot_raw_result = read_entry('backtest','plot_raw_result')
    mf = read_entry('backtest','mf')
    capital = read_entry('backtest','capital')
    shrink_by_high_cond = flt(read_entry('backtest','shrink_by_high_cond'))
    shrink_by_lower_cond = flt(read_entry('backtest','shrink_by_lower_cond'))

    df = backtest(types,sides,algo_str)

    save_test(df)
    summa = df['opt_sum'].iloc[-1] if trades > 0 else exit('No trades')
    descr_str = '{} {} {} disc {}, hedge {}'.format(ticker, types, sides, disc_prc,hedge_usd)
    limit_str = 'h_lim, %.2f, l_lim %.2f' % (high_opt_price_limit,low_spread_price_limit) if high_opt_price_limit > 0 and low_spread_price_limit > 0 else 'l_lim %.2f' % low_spread_price_limit if low_spread_price_limit > 0 else 'h_lim %.2f' % high_opt_price_limit if high_opt_price_limit > 0 else ''
    cond_str = 'shrink %d, %s' % (shrink_by_lower_cond, limit_str) if shrink_by_lower_cond > 0 else limit_str
    max_dd_val = df.loc[(df['margin_0'] < 0) & (df['lcond'] == 1)]['margin_0'].min() if dd_count > 0 else 0
    max_raw_dd_val = df.loc[df['margin_0'] < 0]['margin_0'].min() if dd_raw_count > 0 else 0
    dd_str = 'dd count %d/%d, val %.2f/%.2f' % (dd_count,dd_raw_count,-max_dd_val,-max_raw_dd_val) if dd_count > 0 or dd_raw_count > 0 else ''
    sum_fmt = 'profit %.2f' % summa if capital in ('','per opt') else 'profit %.2f%%' % summa if capital in ('%','prc') else 'profit/capital $%.2f/$%.2f' % (summa,float(capital))
    per_trade = summa/trades
    res = '%s, per trade %.2f, trades %d/%d, %s' % (sum_fmt, per_trade,trades,max_trades,dd_str)
    txt = '%s, %s\n%s' % (descr_str, cond_str,res)
    if mf == 'fm':
        txt = 'Fri - Mon\n%s' % txt
    plot(df,'quote_date',txt,opt_count=count,fn=fn,stock=stock,plot_raw=plot_raw_result)


if __name__ == '__main__':
    main_proc()
