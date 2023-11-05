#import pandas as pd
#from dateutil.relativedelta import *
import inspect

from pandas import DatetimeIndex

from au import *
import os
import matplotlib.pyplot as plt

def add_days(dt):
    return dt + relativedelta(days=7)

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    if name.find('/') > 0:
        df_path = name
    else:
        df_path = '../devel/%s.csv' % name
    dtf.to_csv(df_path,index=False)
    print('save %s done' % name)
    if stop:
        exit()
def show(df, stop=True, ):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    print(df.head())
    print(df.columns.tolist())
    if stop:
        exit()

def analyze_option():
    date = s2d('2020-02-26')
    exp = s2d('2020-03-04')
    strike = 281
    opts = read_opt(2020,'P')
    opt = opts.loc[(opts['quote_date'] >= date) & (opts['expiration'] == exp) & (opts['strike'] == strike)]
    print(opt[['quote_date','underlying_bid_1545','ask_1545']])
def spy():
    df = pd.read_csv('../data/SPY-yahoo.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['late'] = pd.Series(map(lambda x:add_days(x),df['Date']))
    df_left = df[['Date','Close','late']]
    df_right = df[['Date','Close']]
    df1 = pd.merge(df_left,df_right,left_on='late',right_on='Date')
    df1['delta'] = 100*(df1['Close_x'] - df1['Close_y'])/df1['Close_x']
    m = df1.iloc[df1['delta'].argsort()][-30:]
    print(df1['delta'].max())
    print(m)
def normalize(window):
    return (window - min(window.min())) / (max(window.max()) - min(window.min()))

def make_delta_column(df_in,discount):
    k = (100 - discount) / 100
    df_in['delta'] = (df_in['underlying_ask'] * k - df_in['strike']).abs() * 10.0
    df_in['delta'] = df_in['delta'].astype(int)
    return df_in

def single_opt(opt_date,strike):
    dt_date = s2d(opt_date)
    y = dt_date.year
    yahoo_df = pd.read_csv('../data/QQQ/QQQ-yahoo.csv',index_col=0,parse_dates=['Date'])
    df = pd.read_csv('../data/QQQ/QQQ_CBOE_%s_P.csv' % y,parse_dates=['quote_date','expiration'])
    df = df.loc[df['quote_date'] == dt_date].loc[df['strike'] == strike].loc[df['option_type'] == 'P']
    df = pd.merge(df,yahoo_df,left_on='quote_date',right_on='Date')
    df = df.rename(columns={'quote_date':'date','expiration':'exp','open':'o','high':'h','ask_1545':'1545','ask_eod':'eod','Open':'uopen','underlying_ask_1545':'u1545','underlying_ask_eod':'ueod'})
    df = df[['exp','strike','uopen','o','u1545','1545','ueod','eod']].loc[(df['exp_weekday'] == 5) & (df['days_to_exp']<5)]
    print('date %s' % opt_date)
    print(df)


def add_wrk_days(dt):
    return add_work_days(dt,exp_in)
def add_wrk_days1(dt):
    return add_work_days(dt,1)
#def add_wrk_days2(dt):
#    return add_work_days(dt,2)
#def add_wrk_days3(dt):
#    return add_work_days(dt,3)

#def add_wrk_days4(dt):
    # global exp_in
#    return add_work_days(dt,exp_in)
def lowest_week_price(tick,enter_weekday,show_rows,sort,yr=None):
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (tick,tick))[['Date','Open','Low','Close']]
    df['Date'] = pd.to_datetime(df['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['Date1'] = pd.Series(map(add_wrk_days1,df['Date']))
    df['Date2'] = pd.Series(map(add_wrk_days1, df['Date1']))
    df['Date3'] = pd.Series(map(add_wrk_days1, df['Date2']))
    df['Date4'] = pd.Series(map(add_wrk_days1, df['Date3']))
    df_left = df[['Date','Open','Low','Close','wkd','Date1','Date2','Date3','Date4']]
    how = 'inner'
    df_right1 = df[['Date','Low']].rename(columns={'Date': 'Date1','Low':'Low1'})
    df1 = pd.merge(df_left,df_right1,on='Date1',how=how)
    df_right2 = df[['Date','Low']].rename(columns={'Date': 'Date2','Low':'Low2'})
    df2 = pd.merge(df1,df_right2,on='Date2',how=how)
    df_right3 = df[['Date','Low']].rename(columns={'Date': 'Date3','Low':'Low3'})
    df3 = pd.merge(df2,df_right3,on='Date3',how=how)
    df_right4 = df[['Date','Low','Close']].rename(columns={'Date': 'Date4','Low':'Low4','Close':'Close4'})
    df4 = pd.merge(df3,df_right4,on='Date4',how=how)
    df = df4.loc[df4.wkd == enter_weekday].copy()
    df['dd0'] = df.Open.sub(df.Low)
    df['dd1'] = df.Open.sub(df.Low1)
    df['dd2'] = df.Open.sub(df.Low2)
    df['dd3'] = df.Open.sub(df.Low3)
    df['dd4'] = df.Open.sub(df.Low4)
    df['dd_exp'] = df.Open.sub(df.Close4)
    df['dd_Low_max'] = df.Open.sub(df[['Low','Low1','Low2','Low3','Low4']].min(axis=1))
    df['dd_Low_prc'] = (df['dd_Low_max']/df.Open) * 100
    df['dd_exp_max'] = df.Open.sub(df.Close4)
    df['dd_exp_prc'] = (df['dd_exp_max']/df.Open) * 100
    if yr[:1] == '>':
        yr = int(yr[1:])
        bd = s2d('%d-01-01' % yr)
        df = df.loc[df['Date'] > bd]
    else:
        yr = int(yr)
        ed = s2d('%d-01-01' % (yr + 1))
        bd = s2d('%d-01-01' % yr)
        df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]

    df = df.sort_values('dd_%s_prc' % sort)[['Date','Open','Low1','Low2','Low3','Low4','Close4','dd0','dd1','dd2','dd3','dd4','dd_Low_max','dd_Low_prc','dd_exp_max','dd_exp_prc','dd_exp','Date1','Date2','Date3','Date4']]
    df = df[-show_rows:]
    df['worst_day'] = ''
    df['worst_dd'] = 0.
    for r,s in df[['dd0','dd1','dd2','dd3','dd4']].iterrows():
        max_dd = 0
        worst_wd = ''
        for wd,dd in s.items():
            if dd > max_dd:
                worst_wd = wd
                max_dd = dd
        df.at[r,'worst_day'] = worst_wd
    print(df[['Date','dd_Low_prc','dd_exp_prc','worst_day']])
    save(df)
def print_df(df):
    row = df.iloc[0]
    columns = df.columns
    s = ''
    for c in range(len(row)):
        v = row.iloc[c]
        if isinstance(v, datetime):
            add = '%10s ' % columns[c]
        elif isinstance(v, float):
            add = '%6s ' % columns[c]
        else:
            add = ''
        s = s + add
    print(s)
    for index, row in df.iterrows():
        s = ''
        for c in row:
            if isinstance(c, datetime):
                add = d2s(c)+' '
            elif isinstance(c,float):
                add = '%6.2f ' % c
            else:
                add = ''
            s = s+add
        print(s)
        # print('%s %6.2f %s' % (d2s(row.iloc[1]),row.iloc[2],d2s(row.iloc[3])))

def max_move(tick,enter_weekday,show_rows,yr=None,sort='prc_oc'):
    if path.exists('../data/%s' % ticker):
        folder = ticker
    else:
        folder = 'other'
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (folder,tick),parse_dates=['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['exp_Date'] = pd.Series(map(lambda x: add_wrk_days(x),df['Date']))
    if not yr == '':
        if yr[4] == '+':
            yr = int(yr[0:4])
            bd = s2d('%d-01-01'%yr)
            df = df.loc[df['Date'] > bd]
        else:
            yr = int(yr)
            ed = s2d('%d-01-01' % (yr + 1))
            bd = s2d('%d-01-01'%yr)
            df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]

    df_in = df[['Date','Open','Close','wkd','exp_Date']]
    df_exit = df[['Date','High','Low','Close','wkd']]
    df = pd.merge(df_in,df_exit,left_on='exp_Date',right_on='Date')
    df = df.loc[df['wkd_x'] == enter_weekday]
    df['delta_low'] = df['Open'] - df['Low']
    df['delta_close'] = df['Open'] - df['Close_y']
    df['delta_high'] = df['Open'] - df['High']
    df['delta_cc'] = df['Close_x'] - df['Close_y']
    # df = df.loc[df.Date_x > s2d('2009-05-04')].reset_index(drop=True)
    #df['wkd_x'] = pd.Series(map(str,df['wkd_x']))
    #df['wkd_y'] = pd.Series(map(str,df['wkd_y']))
    #df['wkd'] = df['wkd_x'] + df['wkd_y']
    df['prc_l'] = 100*(df['delta_low'])/df['Open']
    df['prc_h'] = 100*(df['delta_high'])/df['Open']
    df['prc_oc'] = 100*(df['delta_close'])/df['Open']
    df['prc_cc'] = 100*(df['delta_cc'])/df['Close_x']
    df = df.rename(columns={'Date_x':'dt_in','Open':'enter','Date_y':'dt_out','Close_y':'out_c'})
    df_down = df[['dt_in','enter','dt_out','Low','out_c','prc_l','prc_cc','prc_oc']]
    df_up = df[['dt_in','enter','dt_out','High','out_c','prc_h','prc_cc','prc_oc']]
    down = (df_down.sort_values(sort)[-show_rows:]).reset_index()
    up = (df_up.sort_values(sort)[:show_rows]).reset_index()
    pd.set_option('display.precision', 2)
    print('------------UP---------------')
    print_df(up)
    print('------------DOWN---------------')
    print_df(down)
def scale_stock(df):
    stock = 'underlying'
    if 'atm' in df.columns:
        cols = ['atm']
    elif 'otm' in df.columns:
        cols = ['otm']
    else:
        cols = ['ma']
    dfnn = df[~df.isnull().any(axis=1)]
    opt_min = dfnn[cols].to_numpy().min()
    opt_max = dfnn[cols].to_numpy().max()
    under_min = dfnn[stock].to_numpy().min()
    under_max = dfnn[stock].to_numpy().max()
    df[stock] = df[stock] * (opt_max - opt_min) / (under_max - under_min)
    under_min = df[stock].to_numpy().min()
    df[stock] = df[stock] - under_min + opt_min
    return df

def from_1545_to_eod():
    disc_usd = 2
    max_price = 0.01
    df = pd.read_csv('../data/SPY/SPY_CBOE_2020_P.csv',parse_dates=['quote_date'])
    df = df.loc[df['days_to_exp'] == 0]
    df['delta'] = (df['underlying_bid_1545'] - disc_usd - df['strike']) * 100
    df['delta'] = df['delta'].astype(int)
    df = df.loc[df['delta'] > 0]
    df_min_delta = df.groupby(['quote_date'])['delta'].min().to_frame()
    df = pd.merge(df_min_delta, df, on=['quote_date', 'delta']).sort_values(['quote_date', 'expiration'])
    df = df.drop_duplicates(subset=['quote_date', 'expiration'])
    df['dd'] = (df['underlying_bid_1545'] - df['underlying_bid_eod'])
    df = df.loc[df['ask_1545'] <= max_price]
    df['long_profit'] = df['bid_eod'] - df['ask_1545']
    df = df.sort_values(['dd'])
    df = df[['quote_date','strike','underlying_bid_1545','ask_1545','underlying_bid_eod','bid_eod','dd','long_profit']]
    # save(df)
    print(df[['quote_date','ask_1545','bid_eod','dd','long_profit']].tail(10))
    print(df['long_profit'].sum())

def make_datafile():
    columns = ['quote_date', 'expiration', 'strike', 'open', 'ask_1545', 'underlying_bid_1545', 'days_to_exp']
    df0 = pd.read_csv('../data/QQQ/QQQ_CBOE_2020_PC.csv')
    df0 = df0.loc[(df0['option_type'] == 'P') & (df0['exp_weekday'] == 5) & (df0['days_to_exp'] <= 4)][columns]
    df1 = pd.read_csv('../data/QQQ/QQQ_CBOE_2021_PC.csv')
    df1 = df1.loc[(df1['option_type'] == 'P') & (df1['exp_weekday'] == 5) & (df1['days_to_exp'] <= 4)][columns]
    df_20_21 = pd.concat([df0,df1])
    df0 = pd.read_csv('../data/QQQ/QQQ_CBOE_2022_PC.csv')
    df0 = df0.loc[(df0['option_type'] == 'P') & (df0['exp_weekday'] == 5) & (df0['days_to_exp'] <= 4)][columns]
    df1 = pd.read_csv('../data/QQQ/QQQ_CBOE_2023_PC.csv')
    df1 = df1.loc[(df1['option_type'] == 'P') & (df1['exp_weekday'] == 5) & (df1['days_to_exp'] <= 4)][columns]

    df_22_23 = pd.concat([df0,df1])
    df_20_23 = pd.concat([df_20_21,df_22_23])
    save(df_20_23,'../data/QQQ/QQQ_P.csv')

def atm_price(disc,bd_str,ma_per):
    timing = 'open'
    if ma_per > 0:
        plot_columns = ['underlying','ma']
    else:
        plot_columns = ['atm','otm','underlying']
    if timing == '1545':
        open_price = 'ask_1545'
    else:
        open_price = 'open'

    bd = s2d(bd_str)
    if not os.path.exists('../data/QQQ/QQQ_P.csv'):
        make_datafile()
    df = pd.read_csv('../data/QQQ/QQQ_P.csv')

    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df = df.loc[df['days_to_exp'] == 4].drop(columns=['days_to_exp'])
    if timing == 'open':
        df_under = pd.read_csv('../data/QQQ/QQQ-yahoo.csv')
        df_under['Date'] = pd.to_datetime(df_under['Date'])
        df = pd.merge(df,df_under,left_on='quote_date',right_on='Date',how='outer')
        df = df.rename(columns={'Open':'underlying','open':'enter'})
        df = df.drop(columns={'underlying_bid_1545','ask_1545','Date','High','Low','Close','Adj Close','Volume'})
    else:
        df = df.rename(columns={'underlying_bid_1545':'underlying','ask_1545':'enter'})
        df = df.drop(columns={'open'})
    df['delta_atm'] = (df['underlying'] - df['strike']) * 100
    df['delta_otm'] = (df['underlying'] * (100 - disc)/100 - df['strike']) * 100

    df_atm = df.loc[df['delta_atm'] >= 0].copy()
    df_atm['delta_atm'] = df_atm['delta_atm'].astype(int)
    df_min = df_atm.groupby(['quote_date','expiration'])['delta_atm'].min().to_frame()
    df_atm = pd.merge(df_atm,df_min,on=['quote_date','expiration','delta_atm']).drop_duplicates(subset=['quote_date'])
    df_atm['enter'] = df_atm['enter'] - (df_atm['underlying'] - df_atm['strike'])
    df_atm = df_atm[['quote_date','expiration','enter','underlying']]
    df_otm = df.loc[df['delta_otm'] >= 0].copy()
    df_otm['delta_otm'] = df_otm['delta_otm'].astype(int)
    df_min = df_otm.groupby(['quote_date','expiration'])['delta_otm'].min().to_frame()
    df_otm = pd.merge(df_otm,df_min,on=['quote_date','expiration','delta_otm']).drop_duplicates(subset=['quote_date'])
    df_otm = df_otm[['expiration','enter']]
    df = pd.merge(df_atm,df_otm,on='expiration').rename(columns={'enter_x':'atm','enter_y':'otm'})
    save(df,'otm-%d' % disc)
    cols = ['expiration'] + plot_columns
    df['ma'] = df['otm'].rolling(ma_per).mean()
    df = df.loc[df['expiration'] > bd][cols]
    df = scale_stock(df)
    df = df.set_index('expiration')
    df = df[plot_columns]
    ax = df.plot(figsize=(11, 7))
    freq = 'M' if len(df) > 10 else 'D'
    xtick: DatetimeIndex = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    ax.set_xticks(xtick, minor=False)  # play with parameter
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    plt.savefig('../devel/%s.png' % open_price)
    plt.show()

if __name__ == '__main__':
    ticker = read_entry('research','ticker')
    ent_weekday = int(read_entry('research','enter_weekday'))
    exp_in = int(read_entry('research','expires_in'))
    show_r = int(read_entry('research','show_rows'))
    year = read_entry('research','year')
    procedure = read_entry('research','procedure')
    arg_1 = read_entry('research','arg_1')
    arg_2 = read_entry('research','arg_2')
    arg_3 = read_entry('research','arg_3')

    if procedure == '1':
        max_move(tick=ticker, enter_weekday=ent_weekday, show_rows=show_r, yr=year, sort=arg_1)
    elif procedure == '2':
        lowest_week_price(tick=ticker,enter_weekday=ent_weekday,show_rows=show_r,sort=arg_1,yr=year)
    elif procedure == '3':
        atm_price(disc=float(arg_1),bd_str=arg_2,ma_per=int(arg_3))
    elif procedure == '4':
        single_opt(opt_date='2020-03-20',strike=177)
    elif procedure == '5':
        from_1545_to_eod()
