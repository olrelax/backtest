import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import inspect

draw_or_show = 'show'
start_date = '2020-01-01'
type1,type2,side1,side2 = 'C','P',1,1
premium_limit = 100
fn = ''
plot_under = True
def plot(df):
    do_2 = type2 in ('P', 'C')
    if plot_under:
        opt_min = df[['sum_1','sum_2','sum']].to_numpy().min() if do_2 else df['sum_1'].min()
        opt_max = df[['sum_1','sum_2','sum']].to_numpy().max() if do_2 else df['sum_1'].max()
        under_min = df['under_1_out'].to_numpy().min()
        under_max = df['under_1_out'].to_numpy().max()
        df['under_1_out'] = df['under_1_out'] * (opt_max-opt_min)/(under_max - under_min)
        under_min = df['under_1_out'].to_numpy().min()
        df['under_1_out'] = df['under_1_out'] - under_min + opt_min
    plt.figure(figsize=(11, 7))
    if do_2:
        if plot_under:
            plt.plot(df['expiration'],df[['under_1_out','sum_1','sum_2','sum']],label=['under','sum_1','sum_2','sum'])
        else:
            plt.plot(df['expiration'],df[['sum_1','sum_2','sum']],label=['sum_1','sum_2','sum'])
    else:
        if plot_under:
            plt.plot(df['expiration'],df[['under_1_out','sum_1']],label=['under','sum_1'])
        else:
            plt.plot(df['expiration'],df['sum_1'],label=['sum_1'])
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
    fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(fn)
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
        o['profit'] = (o['bid_1545_x'] - o['ask_1545_y']).sub(0.021)
    else:
        o['profit'] = (o['bid_1545_y'] - o['ask_1545_x']).sub(0.021)
    o = o[['quote_date','expiration','strike','underlying_bid_1545_x','bid_1545_x','ask_1545_x','ask_1545_x','exp_weekday','days_to_exp','underlying_bid_1545_y','bid_1545_y','ask_1545_y','profit']]
    o.sort_values(['quote_date','expiration'])
    return o

def backtest(discount_1,discount_2):
    df = get_df(discount_1,side1,type1)
    df = df.rename(columns={'underlying_bid_1545_x':'under_1_in','bid_1545_x':'bid_1_in','ask_1545_x':'ask_1_in','underlying_bid_1545_y':'under_1_out','bid_1545_y':'bid_1_out','ask_1545_y':'ask_1_out','profit':'profit_1'})
    df = df.loc[df['bid_1_in'] < premium_limit]
    df['sum_1'] = df['profit_1'].cumsum(axis=0)
    if type2 not in ('P','C'):
        return df
    df2 = get_df(discount_2,side2,type2)
    df2 = df2.rename(columns={'underlying_bid_1545_x':'under_2_in','bid_1545_x':'bid_2_in','ask_1545_x':'ask_2_in','underlying_bid_1545_y':'under_2_out','bid_1545_y':'bid_2_out','ask_1545_y':'ask_2_out','profit':'profit_2'})
    df = pd.merge(df,df2,on='expiration')
    df['sum_2'] = df['profit_2'].cumsum(axis=0)
    df['sum'] = df['sum_1'] + df['sum_2']
    return df


def do_backtests():
    global draw_or_show, start_date, type1, type2, side1, side2, premium_limit,fn,plot_under
    type1 = 'C'
    type2 = 'C'
    side1 = 'L'
    side2 = 'S'
    a = 'start 3 9'
    premium_limit = 5
    start_date = '2018-01-01'
    draw_or_show = 'show'
    plot_under = True
    while True:
        if a[:5] == 'start':
            a = a[6:]
        else:
            a = input('>')
        if a == 'q' or len(a) == 0:
            break
        else:
            p = a.split(' ')
            disc_s = int(p[0])
            disc_l = int(p[1]) if len(p) > 1 else 0
        df = backtest(disc_s, disc_l)
        fn = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
        ini_str = 'type%s side%s disc%d, type%s side%s param%d, lim %d' % (type1,side1,disc_s,type2,side2,disc_l,premium_limit)
        ini = open('../out/i-%s.txt' % fn,'w')
        print(ini_str,file=ini)
        ini.close()
        # noinspection PyTypeChecker
        df.to_csv('../out/e-%s.csv' % fn, index=False)
        plot(df)
        if not draw_or_show == 'draw':
            break

if __name__ == '__main__':
    do_backtests()
