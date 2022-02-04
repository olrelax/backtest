import pandas as pd
from au import s2d
import matplotlib.pyplot as plt
from datetime import datetime

from inspect import currentframe, getframeinfo
from au import fl
def plot(df,txt):
    ax = df.plot(figsize=(12, 7), subplots=False,title=txt)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    now = datetime.strftime(datetime.now(), '%d-%-H-%M-%S')
    plt.savefig('../out/%s.png' % now)
    plt.show()


def get_df(df,disc,side,wd):
    weekday = wd
    days2exp = 7
    o = df.loc[df['weekday'] == weekday]
    o = o.loc[o['days_to_exp'] == days2exp]
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
        o['profit_s'] = o['bid_1545_x'] - o['ask_1545_y']
        o['sum_s'] = o['profit_s'].cumsum(axis=0)
    else:
        o['profit_l'] = o['bid_1545_y'] - o['ask_1545_x']
        o['sum_l'] = o['profit_l'].cumsum(axis=0)

    o.sort_values(['quote_date','expiration'])
    return o
def backtest():

    discount_s = 15
    discount_l = 20
    wd = 1
    bd = s2d('2020-01-01')
    fl(getframeinfo(currentframe()))
    fn = '../data/week.csv'
    df = pd.read_csv(fn, index_col=0)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df = df.loc[df['quote_date'] > bd]
    short = get_df(df,discount_s,'S',wd)
    long = get_df(df,discount_l,'L',wd)
    short_plot = short[['expiration','sum_s']].set_index('expiration')
    long_plot = long[['expiration','sum_l']].set_index('expiration')
    hedged_plot = pd.merge(short_plot,long_plot,on='expiration')
    hedged_plot['sum'] = hedged_plot['sum_s'] + hedged_plot['sum_l']
    txt = 'discS=%d, discL=%d, wd=%d' % (discount_s,discount_l,wd)
    plot(hedged_plot,txt)


if __name__ == '__main__':
    backtest()
