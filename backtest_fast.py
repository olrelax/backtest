import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect
from au import s2d
from os import system
draw_or_show = ''
start_year = 0
before_date = ''
premium_max = 1.
fn = ''
plot_under = None
single_pos_len = 0
algo = ''
comm = 0
premium_min = 100.0
strike_loss_limit = -100
ylim_bottom = -100
ylim_top = 100


def normalize(df):
    opt_min = df[['sum_1','sum_2','sum']].to_numpy().min()
    opt_max = df[['sum_1','sum_2','sum']].to_numpy().max()
    under_min = df['under_1_out'].to_numpy().min()
    under_max = df['under_1_out'].to_numpy().max()
    df['under_1_out'] = df['under_1_out'] * (opt_max-opt_min)/(under_max - under_min)
    under_min = df['under_1_out'].to_numpy().min()
    df['under_1_out'] = df['under_1_out'] - under_min + opt_min
    return df

def plot(df,types,sides,params):
    count = int(df.shape[1]/single_pos_len)
    if count == 1:
        dfp = df[['expiration','sum_0']]
    else:
        cols = 'expiration,'
        for i in range(count):
            cols = cols + 'sum_%d,' % i
        cols = cols + 'sum'
        dfp = df[cols.split(',')]
    dfp = dfp.set_index('expiration')
    txt = '{}, type {}, side {},param {},lim max {},lim min {} '.format(algo,types,sides,params,premium_max,premium_min)
    ax = dfp.plot(figsize=(11,7), title=txt)
    xtick = pd.date_range(start=dfp.index.min(), end=dfp.index.max(), freq='M')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    ax.set_ylim(ylim_bottom,ylim_top)
    plt.savefig('../out/c-%s.png' % fn)

    if draw_or_show == 'draw':
        plt.draw()
    else:
        plt.show()
    plt.pause(0.0001)
    if draw_or_show == 'draw':
        plt.close()

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
def get_sold(price):
    return 0 if price < 0.0101 else price
def read_opt_file(ofn):
    df = pd.read_csv(ofn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    return df
def get_strike_loss(df):
    df_loss = df.loc[df['strike_0'] - df['under_in_0'] > strike_loss_limit].copy()
    df_loss['str_loss'] = df_loss['strike_0'] - df_loss['under_in_0']
    df_loss = df_loss.drop_duplicates(subset=['expiration'])
    return df_loss

def get_df_for_side(param,side,opt_type):
    bd = datetime.strptime('%d-01-01' % start_year,'%Y-%m-%d')
    ed = datetime.strptime(before_date,'%Y-%m-%d')
    opts_fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(opts_fn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[(df['quote_date'] > bd) & (df['quote_date'] < ed)]

    df_in = df.loc[df['days_to_exp'] > 0].copy()
    if algo == 'dist':
        dist = -param if opt_type == 'C' else param
        df_in['delta'] = (df_in['underlying_ask_1545'].sub(dist).sub(df_in['strike']).abs()*10.0)
    elif algo == 'disc':
        disc = -param if opt_type == 'C' else param
        k = (100-disc)/100
        df_in['delta'] = (df_in['underlying_ask_1545']*k - df_in['strike']).abs() * 10.0
    elif algo == 'price':
        df_in['delta'] = df_in['bid_1545'].sub(param).abs()*100
    else:
        exit('algo?')
    df_in['delta'] = df_in['delta'].astype(int)
    s = df_in.groupby(['expiration'])['delta'].min()
    s = s.to_frame()
    m = pd.merge(s,df_in,on=['expiration','delta']).sort_values(['quote_date','expiration']).drop_duplicates(subset=['quote_date','expiration'])
    o_out = df.loc[df['quote_date'] == df['expiration']]
    o_out = o_out[['expiration','strike','underlying_bid_1545','underlying_ask_1545','ask_1545','bid_1545','ask_eod','bid_eod']]
    o = pd.merge(m,o_out, on=['expiration','strike'])
    if side == 'S':
        o['profit'] = (o['bid_1545_x'] - pd.Series(map(get_sold,o['ask_eod_y']))) - comm
    else:
        o['profit'] = (pd.Series(map(get_sold,o['bid_eod_y'])) - o['ask_1545_x']) - comm
    o = o[['quote_date','expiration','strike','underlying_ask_1545_x','bid_1545_x','ask_1545_x','exp_weekday','days_to_exp','underlying_bid_1545_y','bid_1545_y','ask_1545_y','profit']]
    o.sort_values(['quote_date','expiration'])
    return o
def get_df_between(df_in2exp,side,tp,i):
    side_sign = 1. if side == 'S' else -1.
    df_in2exp['pair_in'] = df_in2exp['quote_date'].astype(str)+df_in2exp['expiration'].astype(str)
    df_all = read_opt_file('../data/SPY_CBOE_2020-2022_%s.csv' % tp)
    df_all = df_all.loc[df_all.days_to_exp < 8]

    df_all = df_all.rename(columns={'strike':'strike_%d' % i})
    df_mix = df_all.merge(df_in2exp,on=['expiration','strike_%d' % i]).sort_values(['expiration','quote_date_x'])
    df_between = df_mix[(~df_mix.pair_all.isin(df_in2exp.pair_in))].sort_values(['expiration','quote_date_x'])
    df_between = df_between.loc[~(df_between['quote_date_x'] == df_between['expiration'])]
    df_between = df_between[['quote_date_x', 'expiration', 'underlying_ask_1545', 'strike_%d' % i, 'bid_1545', 'ask_1545']]
    df_between = df_between.rename(
        columns={'quote_date_x':'quote_date', 'underlying_ask_1545': 'under_in_%d' % i, 'bid_1545': 'bid_out_%d' % i,
                 'ask_1545': 'ask_out_%d' % i})
    df_between = df_between.merge(df_in2exp[['expiration','strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i]],on=['expiration','strike_%d' % i])
    df_between['under_out_%d' % i] = df_between['under_in_%d' % i]         # just mirroring for compatibility with df_in2exp
    df_between = df_between[['quote_date','expiration','under_in_%d' % i,'strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,'under_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i]]
    df_between['profit_%d' % i] = (df_between['bid_in_%d' % i] - df_between['ask_out_%d' % i]) * side_sign
    df_between = get_strike_loss(df_between)
    return df_between



def backtest(types,sides,params):
    global single_pos_len
    count = min(len(types),len(sides),len(params))
    df = [{}]

    for i in range(count):
        print('get_in2exp')
        df_in2exp = get_df_for_side(params[i],sides[i],types[i])
        df_in2exp = df_in2exp.rename(columns={'strike':'strike_%d' % i,'underlying_ask_1545_x':'under_in_%d' % i,'bid_1545_x':'bid_in_%d' % i,'ask_1545_x':'ask_in_%d' % i,'underlying_bid_1545_y':'under_out_%d' % i,'bid_1545_y':'bid_out_%d' % i,'ask_1545_y':'ask_out_%d' % i,'profit':'profit_%d' % i})
        df_in2exp = df_in2exp[['quote_date','expiration','under_in_%d' % i,'strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,'under_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i,'profit_%d' % i]]
        save(df_in2exp)
        df_between = get_df_between(df_in2exp,sides[i],types[i],i)
        df_in2exp = df_in2exp.drop(columns={'pair_in'})
        df_cont = df_in2exp.append(df_between,ignore_index=True).sort_values(['expiration','quote_date'])
        df_cont = df_cont.drop_duplicates(subset=['expiration'],keep='last')      # drop expiration record if exit occurred before

        single_pos_len = df_cont.shape[1] - 1 if i == 0 else single_pos_len
        df = df_cont if i == 0 else pd.merge(df,df_cont,on='expiration')
    df = df.loc[(df['bid_in_0'] < premium_max) & (df['bid_in_0'] > premium_min)].copy()

    for i in range(count):
        df['sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df
def save_test(df,types,sides,params):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn,'w')
    print('type {},sides{},params{}, max {}, min {}, str.loss {}'.format(types,sides,params,premium_max,premium_min,strike_loss_limit),file=ini)
    ini.close()
    # noinspection PyTypeChecker
    df.to_csv('../out/e-%s.csv' % fn, index=False)


def backtests():
    global before_date,draw_or_show, start_year,  premium_max,fn,plot_under,algo,premium_min,strike_loss_limit
    types = ['P','P']
    sides = ['S','L']
    params = [8]
    algo = 'disc'
    premium_max = 200.5
    premium_min = 0.00
    strike_loss_limit = 0
    start_year = 2020
    before_date = '2021-01-01'
    plot_under = False
    draw_or_show = 'show'
    df = backtest(types,sides,params)
    save_test(df,types,sides,params)
    plot(df,types,sides,params)
    if draw_or_show == 'draw':
        input('pause >')

if __name__ == '__main__':
    backtests()
