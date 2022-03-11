import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect
from au import read_opt_file
from functions import get_df_between_1,get_strike_loss,save
from os import system
draw_or_show = ''
start_year = 0
before_date = ''
fn = ''
plot_under = None
single_pos_len = 0
algo = ''
comm = 0
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
    txt = '{}, type {}, side {},param {}, str_loss_lim{}'.format(algo,types,sides,params,strike_loss_limit)
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
def save_test(df,types,sides,params):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn,'w')
    print('type {},sides{},params{}, str_loss_lim {}'.format(types,sides,params,strike_loss_limit),file=ini)
    ini.close()
    # noinspection PyTypeChecker
    df.to_csv('../out/e-%s.csv' % fn, index=False)

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

#def save(dtf,arg_name=None):
#    name = get_name(dtf)[0] if arg_name is None else arg_name
#    print('save',name)
#    dtf.to_csv('../devel/%s.csv' % name,index=True)
def get_sold(price):
    return 0 if price < 0.0101 else price
#def read_opt_file(ofn):
#    df = pd.read_csv(ofn)
#    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
#    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
#    return df
#def get_strike_loss(df,i,field):
#    df_loss = df.copy()
#    # df_loss['str_loss_%d' % i] = df_loss['strike_%d' % i] - df_loss['under_bid_in_%d' % i]
#    df_loss['str_loss_%d' % i] = df_loss['strike_%d' % i] - df_loss['%s_%d' % (field,i)]
#    df_loss = df_loss.loc[df_loss['str_loss_%d' % i] > strike_loss_limit]
#    df_loss = df_loss.drop_duplicates(subset=['expiration'])

#    return df_loss
#def show(df,stop=True):
#    name = get_name(df)[0]
#    print('-----------------%s------------' % name)
#    print(df.info())
#    if stop:
#        exit()
def get_in2exp(param,side,opt_type,i):
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
    m = m[['quote_date','expiration','strike','underlying_bid_1545','underlying_ask_1545','bid_1545','ask_1545']]
    o_out = df.loc[df['quote_date'] == df['expiration']]
    o_out = o_out[['expiration','strike','underlying_bid_1545','underlying_ask_1545','bid_1545','ask_1545','underlying_bid_eod','underlying_ask_eod','bid_eod','ask_eod']]
    o_out = o_out.rename(columns={'underlying_bid_1545':'under_bid_1545_out_%d'%i,'underlying_ask_1545':'under_ask_1545_out_%d'%i,'bid_1545':'bid_1545_out_%d'%i,'ask_1545':'ask_1545_out_%d'%i})
    o = pd.merge(m,o_out, on=['expiration','strike'])
    if side == 'S':
        o['margin'] = (o['bid_1545'] - pd.Series(map(get_sold,o['ask_eod'])))
    else:
        o['margin'] = (pd.Series(map(get_sold,o['bid_eod'])) - o['ask_1545'])
    o = o.rename(columns={'strike':'strike_%d' % i,'underlying_bid_1545':'under_bid_in_%d' % i,'underlying_ask_1545':'under_ask_in_%d' % i,
                          'bid_1545':'bid_in_%d' % i,'ask_1545':'ask_in_%d' % i,'underlying_bid_eod':'under_bid_out_%d' % i,
                          'underlying_ask_eod':'under_ask_out_%d' % i,'bid_eod':'bid_out_%d' % i,'ask_eod':'ask_out_%d' % i,
                          'margin':'margin_%d' % i})
    o_loss = get_strike_loss(o,i,'under_bid_1545_out',strike_loss_limit) if side == 'S' else ''
    o = o.drop(columns={'under_bid_1545_out_%d' % i, 'under_ask_1545_out_%d' % i, 'bid_1545_out_%d' % i, 'ask_1545_out_%d' % i})
    if len(o_loss) > 0:
        o_loss = o_loss.drop(columns={'under_bid_out_%d'%i,'under_ask_out_%d'%i,'bid_out_%d'%i,'ask_out_%d'%i})
        o_loss = o_loss.rename(columns={'under_bid_1545_out_%d'%i:'under_bid_out_%d'%i,'under_ask_1545_out_%d'%i:'under_ask_out_%d'%i,
                                        'bid_1545_out_%d'%i:'bid_out_%d'%i,'ask_1545_out_%d'%i:'ask_out_%d'%i})
        o_loss['margin_%d'%i] = o_loss['bid_in_%d'%i] - o_loss['ask_out_%d'%i]
        o = o.append(o_loss,ignore_index=True).sort_values(['quote_date','expiration','str_loss_%d'%i])
        o = o.drop_duplicates(subset=['quote_date','expiration'],keep='first')
    return o
def get_df_between(df_in2exp,side,tp,i):
    side_sign = 1. if side == 'S' else -1.
    df_in2exp['pair_in'] = df_in2exp['quote_date'].astype(str)+df_in2exp['expiration'].astype(str)
    df_all = read_opt_file('../data/SPY_CBOE_2020-2022_%s.csv' % tp)
    df_all = df_all.loc[df_all.days_to_exp < 8]

    df_all = df_all.rename(columns={'strike':'strike_%d' % i})
    df_in2exp2exclude = df_in2exp[['quote_date','expiration','strike_%d' % i,'pair_in']]   # list of contacts lasted till on expiration
    df_mix = df_all.merge(df_in2exp2exclude,on=['expiration','strike_%d' % i])
    df_between = df_mix[(~df_mix.pair_all.isin(df_in2exp2exclude.pair_in))]
    df_between = df_between.loc[~(df_between['quote_date_x'] == df_between['expiration'])]
    # show(df_between)
    df_between = df_between.rename(
        columns={'quote_date_x':'quote_date', 'underlying_bid_1545': 'under_bid_out_%d' % i,'underlying_ask_1545': 'under_ask_out_%d' % i,
                 'bid_1545': 'bid_out_%d' % i,'ask_1545': 'ask_out_%d' % i})
    df_between['under_bid_in_%d' % i] = df_between['under_bid_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    df_between['under_ask_in_%d' % i] = df_between['under_ask_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    # The quote_date in this df is the date of exit due to loss limit, so prices on that date is the out prices.
    # To calculate loss margin we join df_in2exp to get prices at the date of enter
    df_between = df_between.merge(df_in2exp[['expiration','strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i]],on=['expiration','strike_%d' % i])
    df_between = df_between[['quote_date','expiration','strike_%d' % i,'under_bid_in_%d' % i,'under_ask_in_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,
                             'under_bid_out_%d' % i,'under_ask_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i]]
    df_between['margin_%d' % i] = (df_between['bid_in_%d' % i] - df_between['ask_out_%d' % i]) * side_sign
    df_between = get_strike_loss(df_between,i,'under_bid_in',strike_loss_limit)
    return df_between



def backtest(types,sides,params):
    global single_pos_len
    count = min(len(types),len(sides),len(params))
    df = [{}]

    for i in range(count):
        df_in2exp = get_in2exp(params[i],sides[i],types[i],i)
        #if count == 1 and strike_loss_limit is not None:
        if strike_loss_limit is not None and i == 0:
            df_between = get_df_between_1(df_in2exp,sides[i],types[i],i,strike_loss_limit)
            df_in2exp = df_in2exp.drop(columns={'pair_in'})
            df_cont = df_in2exp.append(df_between,ignore_index=True).sort_values(['expiration','quote_date'])
            df_cont = df_cont.drop_duplicates(subset=['expiration'],keep='last')      # drop expiration record if exit occurred before
        else:
            df_cont = df_in2exp
        save(df_cont,'df_cont_%d'%i)
        single_pos_len = df_cont.shape[1] - 1 if i == 0 else single_pos_len
        df = df_cont if i == 0 else pd.merge(df,df_cont,on=['quote_date','expiration'],how='outer')
    # df = df.loc[(df['bid_in_0'] < premium_max) & (df['bid_in_0'] > premium_min)].copy()
    df = df.sort_values(['quote_date','expiration'])
    for i in range(count):
        df['sum_%d' % i] = df['margin_%d' % i].cumsum(axis=0)
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df


def backtests():
    global before_date,draw_or_show, start_year, fn,plot_under,algo,strike_loss_limit
    types = ['P','P']
    sides = ['S','L']
    params = [3,7]
    algo = 'disc'
    strike_loss_limit = 0  # in USD, not in %
    start_year = 2020
    before_date = '2023-01-01'
    plot_under = False
    draw_or_show = 'show'
    df = backtest(types,sides,params)
    df['sum'] = df['sum'].fillna(method='ffill')
    for i in range(len(params)):
        df['sum_%d' % i] = df['sum_%d' % i].fillna(method='ffill')
    save_test(df,types,sides,params)
    plot(df,types,sides,params)
    if draw_or_show == 'draw':
        input('pause >')

if __name__ == '__main__':
    backtests()
