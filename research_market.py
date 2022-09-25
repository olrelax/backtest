from dateutil.relativedelta import *
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
def max_move(tick,enter_weekday,show_rows,yr=None,sort='Low'):
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (tick,tick),parse_dates=['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['exp_Date'] = pd.Series(map(lambda x: add_wrk_days(x),df['Date']))
    if not yr == '':
        yr = int(yr)
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
    t = read_entry('research','ticker')
    ent_weekday = int(read_entry('research','enter_weekday'))
    exp_in = int(read_entry('research','expires_in'))
    show_r = int(read_entry('research','show_rows'))
    year = read_entry('research','year')
#    day_timing = ['Open','Close']
    arg_sort = 'prc_close'
    max_move(tick=t,enter_weekday=ent_weekday,show_rows=show_r,yr=year,sort=arg_sort)
    # lowest_week_price(tick=t,enter_weekday=ent_weekday,show_rows=show_r)
    # single_opt(opt_date='2020-03-20',strike=177)
