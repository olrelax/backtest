#import pandas as pd
from dateutil.relativedelta import *
#import mplfinance as mpf
import inspect
from au import *
import matplotlib.pyplot as plt

def add_days(dt):
    return dt + relativedelta(days=7)

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
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


def comp_pattern():
    df_src = pd.read_csv('../data/SPY-yahoo.csv')
    df_src['Date'] = pd.to_datetime(df_src['Date'])
    dfd = df_src.loc[df_src['Date'] > s2d('2021-01-01')]
    df = dfd[['Open','High','Low','Close']]
    pat_len = 5
    df_len = df.shape[0]
    pattern_d = dfd.iloc[-pat_len:].copy().reset_index(drop=True)
    pattern = pattern_d[['Open','High','Low','Close']]
    pattern = normalize(pattern)

    std_min = 100
    found_window = None
    date_min = None
    i_min = -1
    for i in range(df_len - pat_len * 2 + 1):
        window = df.iloc[i:i+pat_len].copy().reset_index(drop=True)
        window = normalize(window)
        std = pattern.sub(window).std().mean()
        date = dfd['Date'].iloc[i]
        if std < std_min:
            std_min = std
            date_min = date
            i_min = i
            found_window = window
    print(date_min,std_min,i_min)

    series = found_window.append(pattern,ignore_index=True)
    dates = pd.DataFrame({'Date':pd.date_range(start='1/1/2018', periods=2*pat_len)})
    series = pd.merge(dates,series,left_index=True,right_index=True)
    series = series.set_index('Date',drop=True)
    mpf.plot(series,type='ohlc')
    series.to_csv('../out/pat.csv',index=False)
def add_wrk_days(dt):
    return add_work_days(dt,exp_in)
def add_wrk_days1(dt):
    return add_work_days(dt,1)
def add_wrk_days2(dt):
    return add_work_days(dt,2)
def add_wrk_days3(dt):
    return add_work_days(dt,3)

def add_wrk_days4(dt):
    global exp_in
    return add_work_days(dt,exp_in)

def premium_by_price():
    fn = 'UnderlyingOptionsIntervals_900sec_2022-04-04.csv'
    # fn = '0405.csv'
    df = pd.read_csv('../data/QQQ/INTRADAY/%s' % fn)
    df['quote_datetime'] = pd.to_datetime(df['quote_datetime'])
    df['expiration'] = pd.to_datetime(df['expiration'])
    exp = s2d('2022-04-14')
    df = df.loc[(df['option_type'] == 'P') & (df['expiration'] == exp)]
    df = df[['quote_datetime','strike','bid','underlying_ask']]
    df = make_delta_column(df,discount=8)
    min_delta_series = df.groupby(['quote_datetime'])['delta'].min()
    df_min_delta = min_delta_series.to_frame()
    df = pd.merge(df_min_delta, df, on=['quote_datetime','delta']).sort_values('quote_datetime').drop_duplicates(subset=['quote_datetime']).reset_index(drop=True)
    df.plot(x=None,y=['bid','underlying_ask'],subplots=True,figsize=(11, 7))
    plt.show()
    plt.pause(0.0001)
def lowest_week_price(tick,enter_weekday,show_rows):
    df = pd.read_csv('../data/%s/%s-yahoo_wkd.csv' % (tick,tick))[['Date','Open','Low','Close','wkd']]
    df['Date'] = pd.to_datetime(df['Date'])
    # df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
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
    df['dd_Close'] = df.Open.sub(df.Close4)
    df['dd_Low_max'] = df.Open.sub(df[['Low','Low1','Low2','Low3','Low4']].min(axis=1))
    df['dd_Low_prc'] = (df['dd_Low_max']/df.Open) * 100
    df['dd_Close_max'] = df.Open.sub(df.Close4)
    df['dd_Close_prc'] = (df['dd_Close_max']/df.Open) * 100

    df = df.loc[df.Date > s2d('2015-12-31')]
    df = df.sort_values('dd_Low_prc')[['Date','Open','Low1','Low2',	'Low3','Low4','Close4','dd0','dd1','dd2','dd3','dd4','dd_Low_max','dd_Low_prc','dd_Close_max','dd_Close_prc','dd_Close','Date1','Date2','Date3','Date4']]

    df = df[-20:]
    dfp = df[['Date','dd_Low_prc','dd_Close_prc']]
    print(dfp.tail(show_rows))
def max_week_move_0(tick,enter_weekday,show_rows,timing,yr=None):
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (tick,tick),parse_dates=['Date'])
#    df['Date'] = pd.to_datetime(df['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['exp_Date'] = pd.Series(map(add_wrk_days,df['Date']))

    if yr is not None:
        ed = s2d('%d-01-01' % (yr + 1))
        bd = s2d('%d-01-01'%yr)
        df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]

    in_ohlc = timing[0]
    out_ohlc = timing[1]
    df_left = df[['Date',in_ohlc,'wkd','exp_Date']]
    df_right = df[['Date',out_ohlc,'wkd']]
    df1 = pd.merge(df_left,df_right,left_on='exp_Date',right_on='Date')
    df1 = df1.rename(columns={'wkd_x':'wkd_in','wkd_y':'wkd_out'})
    df1 = df1.loc[df1['wkd_x'] == enter_weekday]

    df1['delta'] = df1[in_ohlc] - df1[out_ohlc]
    df1 = df1.loc[df1.Date_x > s2d('2009-05-04')].reset_index(drop=True)
    df1['wkd_in'] = pd.Series(map(str,df1['wkd_in']))
    df1['wkd_out'] = pd.Series(map(str,df1['wkd_out']))
    df1['wkd'] = df1['wkd_x'] + df1['wkd_y']
    df1['delta_prc'] = 100*(df1['delta'])/df1[in_ohlc]
    df1 = df1[['Date_x',in_ohlc,'Date_y',out_ohlc,'wkd','delta','delta_prc']]
    down = df1.sort_values('delta_prc')[-show_rows:]
    # print('-------------------- UP ----------------------------\nenter: %s exit: %s\n' % (enter_price,exit_price), up)
    print('-------------------- DOWN --------------------------\nenter: %s exit: %s enter %d exp in %d \n' % (in_ohlc,out_ohlc,enter_weekday,exp_in),down)
def max_move(tick,enter_weekday,show_rows,yr=None,sort='Low'):
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (tick,tick),parse_dates=['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['exp_Date'] = pd.Series(map(lambda x: add_wrk_days(x),df['Date']))
    if yr is not None:
        ed = s2d('%d-01-01' % (yr + 1))
        bd = s2d('%d-01-01'%yr)
        df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]

    df_in = df[['Date','Open','wkd','exp_Date']]
    df_exit = df[['Date','High','Low','Close','wkd']]
    df1 = pd.merge(df_in,df_exit,left_on='exp_Date',right_on='Date')
    df1 = df1.loc[df1['wkd_x'] == enter_weekday]

    df1['delta_low'] = df1['Open'] - df1['Low']
    df1['delta_close'] = df1['Open'] - df1['Close']
    df1['delta_high'] = df1['Open'] - df1['High']
    df1 = df1.loc[df1.Date_x > s2d('2009-05-04')].reset_index(drop=True)
    df1['wkd_x'] = pd.Series(map(str,df1['wkd_x']))
    df1['wkd_y'] = pd.Series(map(str,df1['wkd_y']))
    df1['wkd'] = df1['wkd_x'] + df1['wkd_y']
    df1['prc_low'] = 100*(df1['delta_low'])/df1['Open']
    df1['prc_high'] = 100*(df1['delta_high'])/df1['Open']
    df1['prc_close'] = 100*(df1['delta_close'])/df1['Open']
    df_down = df1[['Date_x','Open','Date_y','Low','Close','prc_low','prc_close']]
    df_up = df1[['Date_x','Open','Date_y','High','Close','prc_high','prc_close']]
    pd.set_option('display.precision', 2)
    down = df_down.sort_values(sort)[-show_rows:]
    up = df_up.sort_values(sort)[:show_rows]
    print('------------UP---------------')
    print(up)
    print('------------DOWN---------------')
    print(down)

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


if __name__ == '__main__':
    t = 'QQQ'
    ent_weekday = 5
    exp_in = 1
    show_r = 7
    year = None
    day_timing = ['Open','Close']
    arg_sort = 'prc_close'
    max_move(tick=t,enter_weekday=ent_weekday,show_rows=show_r,yr=year,sort=arg_sort)
    # lowest_week_price(tick=t,enter_weekday=ent_weekday,show_rows=show_r)
    # single_opt(opt_date='2020-03-20',strike=177)
