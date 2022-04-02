import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect
from au import read_opt_file
# from functions import get_strike_loss
# draw_or_show, start_year, before_date, fn, plot_under, single_pos_len, \
#    algo, comm, strike_loss_limit, ylim_bottom, ylim_top

from os import system


draw_or_show = ''
start_date = ''
before_date = ''
fn = ''
plot_under = None
single_pos_len = 0
algo = ''
comm = 0
strike_loss_limit = -100
ylim_bottom = -100
ylim_top = 100
premium_limit = 0


def show(df, stop=True, ):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    print(df.head())
    print(df.columns.tolist())
    if stop:
        exit()


def normalize(df):
    opt_min = df[['sum_1', 'sum_2', 'sum']].to_numpy().min()
    opt_max = df[['sum_1', 'sum_2', 'sum']].to_numpy().max()
    under_min = df['under_1_out'].to_numpy().min()
    under_max = df['under_1_out'].to_numpy().max()
    df['under_1_out'] = df['under_1_out'] * (opt_max - opt_min) / (under_max - under_min)
    under_min = df['under_1_out'].to_numpy().min()
    df['under_1_out'] = df['under_1_out'] - under_min + opt_min
    return df


def plot(df, types, sides, params):
    count = int(df.shape[1] / single_pos_len)
    if count == 1:
        dfp = df[['exit_date', 'sum_0']]
    else:
        cols = 'exit_date,'
        for i in range(count):
            cols = cols + 'sum_%d,' % i
        cols = cols + 'sum'
        dfp = df[cols.split(',')]
    dfp = dfp.set_index('exit_date')
    txt = '{}, type {}, side {},param {},\n str_loss_lim {}, premium_lim {}'.format(algo, types, sides, params, strike_loss_limit,premium_limit)
    ax = dfp.plot(figsize=(11, 7), title=txt)
    xtick = pd.date_range(start=dfp.index.min(), end=dfp.index.max(), freq='M')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    ax.set_ylim(ylim_bottom, ylim_top)
    plt.savefig('../out/c-%s.png' % fn)

    if draw_or_show == 'draw':
        plt.draw()
    else:
        plt.show()
    plt.pause(0.0001)
    if draw_or_show == 'draw':
        plt.close()


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

def get_strike_loss(df,i,field):
    df_loss = df.copy()
    df_loss['str_loss_%d' % i] = df_loss['strike_%d' % i] - df_loss['%s_%d' % (field,i)]
    if abs(strike_loss_limit) > 1:
        df_loss = df_loss.loc[df_loss['str_loss_%d' % i] > strike_loss_limit]
    else:
        df_loss = df_loss.loc[df_loss['str_loss_%d' % i] > df_loss['%s_%d' % (field,i)].mul(strike_loss_limit)]
    df_loss = df_loss.drop_duplicates(subset=['expiration'])

    return df_loss

def from_d1_subtract_d2(d1,d2,subset):
    if d2 is not None:
        df = d1.append(d2)
        df = df.drop_duplicates(subset=subset,keep=False) if d2 is not None else d1
    else:
        df = d1
    return df


def get_df_between(df_in2exp,side,tp,i):
    side_sign = 1. if side == 'S' else -1.
    df_all = read_opt_file('../data/SPY_CBOE_2020-2022_%s.csv' % tp)
    df_all = df_all.loc[df_all.days_to_exp < 8]
    df_all = df_all.rename(columns={'strike':'strike_%d' % i})
    df_in2exp2exclude = df_in2exp[['quote_date','expiration','strike_%d' % i]]    # list of contracts ended at expiration
    df_mix = df_all.merge(df_in2exp2exclude,on=['expiration','strike_%d' % i])    # get every days price for selected options
    df_between = df_mix.loc[~(df_mix['quote_date_x'] == df_mix['quote_date_y'])]  # exclude dates when option was bought
    df_between = df_between.loc[~(df_between['quote_date_x'] == df_between['expiration'])]  # exclude expiration dates
    df_between = df_between.rename(
        columns={'quote_date_x':'quote_date', 'underlying_bid_1545': 'under_bid_out_%d' % i,'underlying_ask_1545': 'under_ask_out_%d' % i,
                 'bid_1545': 'bid_out_%d' % i,'ask_1545': 'ask_out_%d' % i})
    df_between = df_between[['quote_date', 'expiration', 'strike_0','bid_out_0', 'ask_out_0', 'under_bid_out_0', 'under_ask_out_0', 'bid_eod', 'ask_eod', 'underlying_bid_eod', 'underlying_ask_eod']]
    df_between['exit_date'] = df_between['quote_date']
    df_between['under_bid_in_%d' % i] = df_between['under_bid_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    df_between['under_ask_in_%d' % i] = df_between['under_ask_out_%d' % i]         # just mirroring for compatibility with df_in2exp
#    show(df_between,False)

    # The quote_date in this df is the date of exit due to loss limit, so the prices on that date is the out prices.
    # To calculate loss margin we join df_in2exp to get prices at the date of enter:
    df_between = df_between.merge(df_in2exp[['quote_date','expiration','strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i]],on=['expiration','strike_%d' % i])
    df_between = df_between.rename(columns={'quote_date_x':'quote_date','quote_date_y':'enter_date'})
    df_between = df_between[['quote_date','expiration','enter_date','exit_date','strike_%d' % i,'under_bid_in_%d' % i,'under_ask_in_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,
                             'under_bid_out_%d' % i,'under_ask_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i]]
    df_between['margin_%d' % i] = (df_between['bid_in_%d' % i] - df_between['ask_out_%d' % i]) * side_sign
    df_between = get_strike_loss(df_between,i,'under_bid_in')
    return df_between


def get_in2exp(param, side, opt_type, i):
    bd = datetime.strptime(start_date, '%Y-%m-%d')
    ed = datetime.strptime(before_date, '%Y-%m-%d') if len(before_date) > 0 else None
    opts_fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(opts_fn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)] if ed is not None else df.loc[df['quote_date'] > bd]

    df_in = df.loc[df['days_to_exp'] > 0].copy()

    if algo == 'dist':
        dist = -param if opt_type == 'C' else param
        df_in['delta'] = (df_in['underlying_ask_1545'].sub(dist).sub(df_in['strike']).abs() * 10.0)
    elif algo == 'disc':
        disc = -param if opt_type == 'C' else param
        k = (100 - disc) / 100
        df_in['delta'] = (df_in['underlying_ask_1545'] * k - df_in['strike']).abs() * 10.0
    elif algo == 'price':
        df_in['delta'] = df_in['bid_1545'].sub(param).abs() * 100
    else:
        exit('algo?')
    df_in['delta'] = df_in['delta'].astype(int)
    s = df_in.groupby(['expiration'])['delta'].min()
    s = s.to_frame()
    m = pd.merge(s, df_in, on=['expiration', 'delta']).sort_values(['quote_date', 'expiration']).drop_duplicates(
        subset=['quote_date', 'expiration'])
    df_in = m[['quote_date', 'expiration', 'strike', 'underlying_bid_1545', 'underlying_ask_1545', 'bid_1545', 'ask_1545']]
    save(df_in)
    df_out = df.loc[df['quote_date'] == df['expiration']]
    df_out = df_out[['expiration', 'strike', 'underlying_bid_1545', 'underlying_ask_1545', 'bid_1545', 'ask_1545',
                   'underlying_bid_eod', 'underlying_ask_eod', 'bid_eod', 'ask_eod']]
    df_out = df_out.rename(
        columns={'underlying_bid_1545': 'under_bid_1545_out_%d' % i, 'underlying_ask_1545': 'under_ask_1545_out_%d' % i,
                 'bid_1545': 'bid_1545_out_%d' % i, 'ask_1545': 'ask_1545_out_%d' % i})
    save(df_out)
    df = pd.merge(df_in, df_out, on=['expiration', 'strike'])
    if side == 'S':
        df['margin'] = (df['bid_1545'] - pd.Series(map(get_sold, df['ask_eod'])))
    else:
        df['margin'] = (pd.Series(map(get_sold, df['bid_eod'])) - df['ask_1545'])
    df = df.rename(columns={'strike': 'strike_%d' % i, 'underlying_bid_1545': 'under_bid_in_%d' % i,
                          'underlying_ask_1545': 'under_ask_in_%d' % i,
                          'bid_1545': 'bid_in_%d' % i, 'ask_1545': 'ask_in_%d' % i,
                          'underlying_bid_eod': 'under_bid_out_%d' % i,
                          'underlying_ask_eod': 'under_ask_out_%d' % i, 'bid_eod': 'bid_out_%d' % i,
                          'ask_eod': 'ask_out_%d' % i,
                          'margin': 'margin_%d' % i})
    df_loss = get_strike_loss(df, i, 'under_bid_1545_out') if side == 'S' and not strike_loss_limit == '' and strike_loss_limit is not None else ''
    df = df.drop(columns={'under_bid_1545_out_%d' % i, 'under_ask_1545_out_%d' % i, 'bid_1545_out_%d' % i,
                        'ask_1545_out_%d' % i})
    if len(df_loss) > 0:
        df_loss = df_loss.drop(
            columns={'under_bid_out_%d' % i, 'under_ask_out_%d' % i, 'bid_out_%d' % i, 'ask_out_%d' % i})
        df_loss = df_loss.rename(columns={'under_bid_1545_out_%d' % i: 'under_bid_out_%d' % i,
                                        'under_ask_1545_out_%d' % i: 'under_ask_out_%d' % i,
                                        'bid_1545_out_%d' % i: 'bid_out_%d' % i,
                                        'ask_1545_out_%d' % i: 'ask_out_%d' % i})
        df_loss['margin_%d' % i] = df_loss['bid_in_%d' % i] - df_loss['ask_out_%d' % i]
        df = df.append(df_loss, ignore_index=True).sort_values(['quote_date', 'expiration', 'str_loss_%d' % i])
        df = df.drop_duplicates(subset=['quote_date', 'expiration'], keep='first')
    df['exit_date'] = df['expiration']
    cols = df.columns.tolist()
    cols.insert(2, 'exit_date')
    cols.pop(-1)
    df['enter_date'] = df['quote_date']
    cols.insert(2, 'enter_date')
    df = df[cols]
    return df


def backtest(types, sides, params):
    global single_pos_len
    count = min(len(types), len(sides), len(params))
    df, df_overpriced = None, None
    for i in range(count):
        df_in2exp = get_in2exp(params[i], sides[i], types[i], i)
        if premium_limit is not None and i == 0 and premium_limit > 0:
            df_overpriced = df_in2exp.loc[df_in2exp['bid_in_0'] > premium_limit]
        if not strike_loss_limit == '' and strike_loss_limit is not None and i == 0:
            df_between = get_df_between(df_in2exp, sides[i], types[i], i)
            df_cont = df_in2exp.append(df_between, ignore_index=True)
            df_cont = df_cont.drop_duplicates(subset=['expiration'],
                                              keep='last')  # drop expiration record if exit occurred before
        else:
            df_cont = df_in2exp
        df_cont = df_cont.sort_values(['exit_date', 'enter_date'])
#        df_cont['sum_%d' % i] = df_cont['margin_%d' % i].cumsum(axis=0)
#        save(df_cont)
        single_pos_len = df_cont.shape[1] - 1 if i == 0 else single_pos_len

        df = df_cont if i == 0 else pd.merge(df, df_cont, on=['exit_date', 'enter_date'], how='outer')
    df = df.rename(columns={'quote_date_x':'quote_date','expiration_x':'expiration'})
    df = from_d1_subtract_d2(df,df_overpriced,['enter_date','expiration'])
    df = df.sort_values(['exit_date', 'enter_date'])

    for i in range(count):
        df['sum_%d' % i] = df['margin_%d' % i].cumsum(axis=0)
        df['sum_%d' % i] = df['sum_%d' % i].fillna(method='ffill')
    for i in range(count):
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df


def backtests():
    global algo, before_date,draw_or_show, start_date, fn, plot_under,strike_loss_limit,premium_limit
    types = ['P', 'P']
    sides = ['S','L']
    params = [12]
    algo = 'disc'
    strike_loss_limit = None  # in USD if > 1 else in %
    start_date = '2021-01-01'
    before_date = '2023-01-01'
    premium_limit = None
    plot_under = False
    draw_or_show = 'show'
    df = backtest(types, sides, params)

    save_test(df, types, sides, params)
    plot(df, types, sides, params)
    if draw_or_show == 'draw':
        input('pause >')


if __name__ == '__main__':
    backtests()
