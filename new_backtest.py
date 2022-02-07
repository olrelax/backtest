import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

draw_or_show = 'show'
start_date = '2020-01-01'
type1,type2,side1,side2 = 'C','P',1,1
bid_1_in_lim = 100
def plot(df):
    plt.figure(figsize=(11, 7))
    if type2 in ('P','C'):
        plt.plot(df['expiration'],df[['sum_1','sum_2','sum']],label=['sum_1','sum_2','sum'])
        plt.legend(loc="lower left")
    else:
        plt.plot(df['expiration'],df['sum_1'])
    plt.xticks(rotation=30)
    plt.grid('on', which='minor')
    plt.grid('on', which='major')
    now = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    plt.savefig('../out/%s.png' % now)
    if draw_or_show == 'draw':
        plt.draw()
    else:
        plt.show()
    plt.pause(0.0001)
    if draw_or_show == 'draw':
        plt.clf()

def save(dtf,name):
    dtf.to_csv('../out/%s.csv' % name,index=False )
def get_df(disc,side,wkd,opt_type):
    global start_date
    days2exp = 7
    bd = datetime.strptime(start_date,'%Y-%m-%d')
    fn = '../data/weekly_%s.csv' % opt_type
    df = pd.read_csv(fn, index_col=0)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[df['quote_date'] > bd]
    if wkd == 1:
        o = df.loc[(df['weekday'] == 1) | (df['weekday'] == 2)]
        o = o.loc[(o['days_to_exp'] == 6) | (o['days_to_exp'] == 7) | (o['days_to_exp'] == 8)]
    else:
        o = df.loc[df['weekday'] == wkd]
        o = o.loc[(o['days_to_exp'] == days2exp)(o['days_to_exp'] == days2exp)(o['days_to_exp'] == days2exp)]
    save(o,'df_in')
    disc = -disc if opt_type == 'C' else disc
    o['delta'] = o['underlying_bid_1545'].sub(disc).sub(o['strike']).abs()*10.0
    o['delta'] = o['delta'].astype(int)
    o = o[['quote_date','expiration','strike','delta','underlying_bid_1545','bid_1545','ask_1545']]
    s = o.groupby(['expiration'])['delta'].min()
    s = s.to_frame()
    m = pd.merge(s,o,on=['expiration','delta']).sort_values(['quote_date','expiration']).drop_duplicates(subset=['quote_date','expiration'])
    o_out = df.loc[df['quote_date'] == df['expiration']]
    o_out = o_out[['expiration','strike','underlying_ask_1545','ask_1545','bid_1545']]
    o = pd.merge(m,o_out, on=['expiration','strike'])
    if side == 'S':
        o['profit'] = (o['bid_1545_x'] - o['ask_1545_y']).sub(0.021)
    else:
        o['profit'] = (o['bid_1545_y'] - o['ask_1545_x']).sub(0.021)
    o.sort_values(['quote_date','expiration'])
    return o

def backtest(discount_1,discount_2,wd):
    df1 = get_df(discount_1,side1,wd,type1)
    df1 = df1[['expiration','underlying_bid_1545','strike','bid_1545_x','ask_1545_x','underlying_ask_1545','bid_1545_y','ask_1545_y','profit']]
    df1 = df1.rename(columns={'underlying_bid_1545':'under_1_in','bid_1545_x':'bid_1_in','ask_1545_x':'ask_1_in','underlying_ask_1545':'under_1_out','bid_1545_y':'bid_1_out','ask_1545_y':'ask_1_out','profit':'profit_1'})
    df1 = df1.loc[df1['bid_1_in'] < bid_1_in_lim]
    if type2 in ('P','C'):
        df2 = get_df(discount_2,side2,wd,type2)
        df2 = df2[['expiration','underlying_bid_1545','strike','bid_1545_x','ask_1545_x','bid_1545_y','underlying_bid_1545','ask_1545_y','profit']]
        df2 = df2.rename(columns={'underlying_bid_1545':'under_2_in','bid_1545_x':'bid_2_in','ask_1545_x':'ask_2_in','underlying_ask_1545':'under_2_out','bid_1545_y':'bid_2_out','ask_1545_y':'ask_2_out','profit':'profit_2'})
        df = pd.merge(df1,df2,on='expiration')
    else:
        df = df1
    return df


def do_backtests():
    global draw_or_show, start_date, type1, type2, side1, side2, bid_1_in_lim
    type1 = 'C'
    type2 = ''
    side1 = 'L'
    side2 = 'L'
    a = 'start 5 25 1'
    bid_1_in_lim = 300
    start_date = '2018-01-01'
    draw_or_show = 'show'

    while True:
        if a[:5] == 'start':
            a = a[6:]
        else:
            a = input('>')
        if a == 'q' or len(a) == 0:
            break
        else:
            p = a.split(' ')
            ds = int(p[0])
            dl = int(p[1]) if len(p) > 1 else 0
            if len(p) == 3:
                wd = int(p[2])
            else:
                wd = 0
        if wd > 0:
            df = backtest(ds, dl, wd)
        else:
            df1 = backtest(ds, dl, 1)
            df2 = backtest(ds, dl, 3)
            df3 = backtest(ds, dl, 5)
            df = df1.append(df2, ignore_index=True)
            df = df.append(df3, ignore_index=True)
            df = df.sort_values('expiration')
        df['sum_1'] = df['profit_1'].cumsum(axis=0)
        if type2 in ('P', 'C'):
            df['sum_2'] = df['profit_2'].cumsum(axis=0)
            df['sum'] = df['sum_1'] + df['sum_2']
            df_plot = df[['expiration', 'sum_1', 'sum_2', 'sum']]
        else:
            df_plot = df
        # noinspection PyTypeChecker
        df.to_csv('../out/df.csv', index=False)
        plot(df_plot)
        if not draw_or_show == 'draw':
            break

if __name__ == '__main__':
    do_backtests()
