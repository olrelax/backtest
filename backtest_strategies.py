import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect
from os import system
draw_or_show = 'show'
start_date = '2020-01-01'
type1,type2,side1,side2 = 'C','P',1,1
premium_limit = 100
fn = ''
plot_under = None
single_pos_len = 0
def normalize(df):
    opt_min = df[['sum_1','sum_2','sum']].to_numpy().min() if do_2 else df['sum_1'].min()
    opt_max = df[['sum_1','sum_2','sum']].to_numpy().max() if do_2 else df['sum_1'].max()
    under_min = df['under_1_out'].to_numpy().min()
    under_max = df['under_1_out'].to_numpy().max()
    df['under_1_out'] = df['under_1_out'] * (opt_max-opt_min)/(under_max - under_min)
    under_min = df['under_1_out'].to_numpy().min()
    df['under_1_out'] = df['under_1_out'] - under_min + opt_min
    return df

def plot(df):
    count = int(df.shape[1]/single_pos_len)
    plt.figure(figsize=(11, 7))
    if count == 1:
        plt.plot(df['expiration'], df['sum_0'],label='sum')
    else:
        cols = ''
        for i in range(count):
            cols = cols + 'sum_%d,' % i
        cols = cols + 'sum'
        plt.plot(df['expiration'], df[cols.split(',')],label=cols.split(','))
    plt.legend(loc='best')


#    df_num = df.drop(columns=['expiration'])
#    df_num = (df_num - df_num.mean()) / df_num.std()

    plt.xticks(rotation=30)
    plt.grid('on', which='minor')
    plt.grid('on', which='major')
    plt.savefig('../out/c-%s.png' % fn)
    if draw_or_show == 'draw':
        plt.draw()
    else:
        plt.show()
    plt.pause(0.0001)
    if draw_or_show == 'draw':
        plt.clf()
def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    dtf.to_csv('../out/%s.csv' % name,index=False)
def get_df(disc,side,opt_type):
    global start_date
    bd = datetime.strptime(start_date,'%Y-%m-%d')
    opts_fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(opts_fn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[df['quote_date'] > bd]
    disc = -disc if opt_type == 'C' else disc
    df_in = df.loc[df['days_to_exp'] > 0].copy()
    df_in['delta'] = (df_in['underlying_bid_1545'].sub(disc).sub(df_in['strike']).abs()*10.0)
    df_in['delta'] = df_in['delta'].astype(int)
    s = df_in.groupby(['expiration'])['delta'].min()
    s = s.to_frame()
    m = pd.merge(s,df_in,on=['expiration','delta']).sort_values(['quote_date','expiration']).drop_duplicates(subset=['quote_date','expiration'])
    o_out = df.loc[df['quote_date'] == df['expiration']]
    o_out = o_out[['expiration','strike','underlying_bid_1545','ask_1545','bid_1545']]
    o = pd.merge(m,o_out, on=['expiration','strike'])
    if side == 'S':
        o['profit'] = (o['bid_1545_x'] - o['ask_1545_y']).sub(0.012)
    else:
        o['profit'] = (o['bid_1545_y'] - o['ask_1545_x']).sub(0.012)
    o = o[['quote_date','expiration','strike','underlying_bid_1545_x','bid_1545_x','ask_1545_x','ask_1545_x','exp_weekday','days_to_exp','underlying_bid_1545_y','bid_1545_y','ask_1545_y','profit']]
    o.sort_values(['quote_date','expiration'])
    return o

def backtest(types,sides,params):
    global single_pos_len
    count = len(types)
    df = [{}]

    for i in range(count):

        dfi = get_df(params[i],sides[i],types[i])
        dfi = dfi.rename(columns={'underlying_bid_1545_x':'under_in_%d' % i,'bid_1545_x':'bid_in_%d' % i,'ask_1545_x':'ask_in_%d' % i,'underlying_bid_1545_y':'under_out_%d' % i,'bid_1545_y':'bid_out_%d' % i,'ask_1545_y':'ask_out_%d' % i,'profit':'profit_%d' % i})
        dfi = dfi[['expiration','under_in_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,'under_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i,'profit_%d' % i]]
        single_pos_len = dfi.shape[1] - 1 if i == 0 else single_pos_len
        dfi['sum_%d' % i] = dfi['profit_%d' % i].cumsum(axis=0)
        df = dfi if i == 0 else pd.merge(df,dfi,on='expiration')
        df['sum'] = df['sum_%d' % i] if i == 0 else df['sum'] + df['sum_%d' % i]
    return df


def do_backtests():
    global draw_or_show, start_date, premium_limit,fn,plot_under
    types = ['C','C']
    sides = ['L','S']
    params = [4,8]
    premium_limit = 5
    start_date = '2018-01-01'
    draw_or_show = 'show'
    plot_under = False
    df = backtest(types,sides,params)
    fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    ini = open('../out/i-%s.txt' % fn,'w')
    print(types,sides,params,file=ini)
    ini.close()
    # noinspection PyTypeChecker
    df.to_csv('../out/e-%s.csv' % fn, index=False)
    plot(df)

if __name__ == '__main__':
    do_backtests()
