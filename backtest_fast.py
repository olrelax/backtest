import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect
from au import read_opt
from os import system
draw_or_show = ''
start_year = 0
type1,type2,side1,side2 = 'C','P',1,1
premium_limit = 1.
fn = ''
plot_under = None
single_pos_len = 0
algo = ''
comm = 0.0105
premium_min = 0.03
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
    txt = '{}, type {}, side {},param {},lim max {},lim min {} '.format(algo,types,sides,params,premium_limit,premium_min)
    ax = dfp.plot(figsize=(10,7), title=txt)
    xtick = pd.date_range(start=dfp.index.min(), end=dfp.index.max(), freq='M')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    ylim_bottom = -60
    ylim_top = 80
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
    dtf.to_csv('../out/%s.csv' % name,index=False)
def get_sold(price):
    return 0 if price < 0.0101 else price
def get_df_for_side(param,side,opt_type):
    bd = datetime.strptime('%d-01-01' % start_year,'%Y-%m-%d')
    opts_fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(opts_fn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[df['quote_date'] > bd]
    df_in = df.loc[df['days_to_exp'] > 0].copy()
    if algo == 'dist':
        dist = -param if opt_type == 'C' else param
        df_in['delta'] = (df_in['underlying_bid_1545'].sub(dist).sub(df_in['strike']).abs()*10.0)
    elif algo == 'disc':
        disc = -param if opt_type == 'C' else param
        k = (100-disc)/100
        df_in['delta'] = (df_in['underlying_bid_1545']*k - df_in['strike']).abs() * 10.0
    elif algo == 'price':
        df_in['delta'] = df_in['bid_1545'].sub(param).abs()*100
    else:
        exit('algo?')
    df_in['delta'] = df_in['delta'].astype(int)
    s = df_in.groupby(['expiration'])['delta'].min()
    s = s.to_frame()
    m = pd.merge(s,df_in,on=['expiration','delta']).sort_values(['quote_date','expiration']).drop_duplicates(subset=['quote_date','expiration'])
    o_out = df.loc[df['quote_date'] == df['expiration']]
    o_out = o_out[['expiration','strike','underlying_bid_1545','ask_1545','bid_1545']]
    o = pd.merge(m,o_out, on=['expiration','strike'])
    if side == 'S':
        o['profit'] = (o['bid_1545_x'] - pd.Series(map(get_sold,o['ask_1545_y']))) - comm
    else:
        o['profit'] = (pd.Series(map(get_sold,o['bid_1545_y'])) - o['ask_1545_x']) - comm
    o = o[['quote_date','expiration','strike','underlying_bid_1545_x','bid_1545_x','ask_1545_x','ask_1545_x','exp_weekday','days_to_exp','underlying_bid_1545_y','bid_1545_y','ask_1545_y','profit']]
    o.sort_values(['quote_date','expiration'])
    return o
def get_df_all_dates(tp):
    opts = None
    for y in range(2022 - start_year):
        y_opts = read_opt('%d' % (start_year + y), tp)
        # y_opts = y_opts.loc[(y_opts['strike'] >= min_strike)(y_opts['strike'] <= max_strike)]
        opts = y_opts if y == 0 else y_opts.append(y_opts,ignore_index=True)
    return opts
def backtest(types,sides,params):
    global single_pos_len
    count = min(len(types),len(sides),len(params))
    df = [{}]

    for i in range(count):

        df_in2exp = get_df_for_side(params[i],sides[i],types[i])
        df_in2exp = df_in2exp.rename(columns={'strike':'strike_%d' % i,'underlying_bid_1545_x':'under_in_%d' % i,'bid_1545_x':'bid_in_%d' % i,'ask_1545_x':'ask_in_%d' % i,'underlying_bid_1545_y':'under_out_%d' % i,'bid_1545_y':'bid_out_%d' % i,'ask_1545_y':'ask_out_%d' % i,'profit':'profit_%d' % i})
        df_in2exp = df_in2exp[['quote_date','expiration','under_in_%d' % i,'strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,'under_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i,'profit_%d' % i]]
#        df_all_dates = get_df_all_dates(types[i])

        single_pos_len = df_in2exp.shape[1] - 1 if i == 0 else single_pos_len
        df = df_in2exp if i == 0 else pd.merge(df,df_in2exp,on='expiration')
    df = df.loc[(df['bid_in_0'] < premium_limit) & (df['bid_in_0'] > premium_min)].copy()

    for i in range(count):
        df['sum_%d' % i] = df['profit_%d' % i].cumsum(axis=0)
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df
def save_test(df,types,sides,params):
    global fn
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn,'w')
    print(types,sides,params,file=ini)
    ini.close()
    # noinspection PyTypeChecker
    df.to_csv('../out/e-%s.csv' % fn, index=False)


def backtests():
    global draw_or_show, start_year, premium_limit,fn,plot_under,algo,premium_min
    types = ['P','P']
    sides = ['S','L']
    params = [12,30]
    algo = 'disc'
    premium_limit = 1.2
    premium_min = 0.1
    start_year = 2020
    plot_under = False
    draw_or_show = 'show'
    df = backtest(types,sides,params)
    save_test(df,types,sides,params)
    plot(df,types,sides,params)
    if draw_or_show == 'draw':
        input('pause >')

if __name__ == '__main__':
    backtests()
