import pandas as pd
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
    dtf.to_csv('../devel/%s.csv' % name,index=False)
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
def add_wrk_days2(dt):
    return add_work_days(dt,2)
def add_wrk_days3(dt):
    return add_work_days(dt,3)

def add_wrk_days4(dt):
    global exp_in
    return add_work_days(dt,exp_in)
def lowest_week_price(tick,enter_weekday,show_rows,arg,yr=None):
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
    if not yr == '':
        yr = int(yr)
        ed = s2d('%d-01-01' % (yr + 1))
        bd = s2d('%d-01-01'%yr)
        df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]
    df = df.sort_values('dd_%s_prc' % arg)[['Date','Open','Low1','Low2','Low3','Low4','Close4','dd0','dd1','dd2','dd3','dd4','dd_Low_max','dd_Low_prc','dd_exp_max','dd_exp_prc','dd_exp','Date1','Date2','Date3','Date4']]

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
        v = row[c]
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

def max_move(tick,enter_weekday,show_rows,yr=None,sort='Low'):
    df = pd.read_csv('../data/%s/%s-yahoo.csv' % (tick,tick),parse_dates=['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['exp_Date'] = pd.Series(map(lambda x: add_wrk_days(x),df['Date']))
    if not yr == '':
        yr = int(yr)
        ed = s2d('%d-01-01' % (yr + 1))
        bd = s2d('%d-01-01'%yr)
        df = df.loc[(df['Date'] > bd) & (df['Date'] < ed)]

    df_in = df[['Date','Open','Close','wkd','exp_Date']]
    df_exit = df[['Date','High','Low','Close','wkd']]
    df1 = pd.merge(df_in,df_exit,left_on='exp_Date',right_on='Date')
    df1 = df1.loc[df1['wkd_x'] == enter_weekday]
    df1['delta_low'] = df1['Open'] - df1['Low']
    df1['delta_close'] = df1['Open'] - df1['Close_y']
    df1['delta_high'] = df1['Open'] - df1['High']
    df1['delta_c_c'] = df1['Close_x'] - df1['Close_y']
    # df1 = df1.loc[df1.Date_x > s2d('2009-05-04')].reset_index(drop=True)
    df1['wkd_x'] = pd.Series(map(str,df1['wkd_x']))
    df1['wkd_y'] = pd.Series(map(str,df1['wkd_y']))
    df1['wkd'] = df1['wkd_x'] + df1['wkd_y']
    df1['prc_l'] = 100*(df1['delta_low'])/df1['Open']
    df1['prc_h'] = 100*(df1['delta_high'])/df1['Open']
    df1['prc_c'] = 100*(df1['delta_close'])/df1['Open']
    df1['prc_cc'] = 100*(df1['delta_c_c'])/df1['Close_x']
    df1 = df1.rename(columns={'Date_x':'dt_in','Open':'enter','Date_y':'dt_out','Close_y':'out_c'})
    df_down = df1[['dt_in','enter','dt_out','Low','out_c','prc_l','prc_c','prc_cc']]
    pd.set_option('display.precision', 2)
    down = (df_down.sort_values(sort)[-show_rows:]).reset_index()

    # up = df_up.sort_values(sort)[:show_rows]
    #print('------------UP---------------')
    #print(up)
    print('------------DOWN---------------')
    print_df(down)
def scale_stock(df):
    stock = 'underlying'
    cols = ['atm']
    opt_min = df[cols].to_numpy().min()
    opt_max = df[cols].to_numpy().max()
    under_min = df[stock].to_numpy().min()
    under_max = df[stock].to_numpy().max()
    df[stock] = df[stock] * (opt_max - opt_min) / (under_max - under_min)
    under_min = df[stock].to_numpy().min()
    df[stock] = df[stock] - under_min + opt_min

    otm_min = df['otm'].to_numpy().min()
    otm_max = df['otm'].to_numpy().max()
    df['otm'] = df['otm'] * (opt_max - opt_min) / (otm_max - otm_min)
    otm_min = df['otm'].to_numpy().min()
    df['otm'] = df['otm'] - otm_min + opt_min

    return df

def atm_price():
    code_part = 4
    timing = 'open'
    disc = 8
    plot = ['atm','otm']
    if timing == '1545':
        openf = 'ask_1545'
    else:
        openf = 'open'
    bd = s2d('2021-01-01')
    columns = ['quote_date', 'expiration', 'strike', 'open', 'ask_1545', 'underlying_bid_1545', 'days_to_exp']
    if code_part in [0,1]:
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
        df = pd.concat([df_20_21,df_22_23])
        # save(df,'df1')
    # elif code_part == 2:
        # df = pd.read_csv('../devel/df1.csv')
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
        df_atm = df_atm[['expiration','enter','underlying']]

        save(df_atm)
        df_otm = df.loc[df['delta_otm'] >= 0].copy()
        df_otm['delta_otm'] = df_otm['delta_otm'].astype(int)
        df_min = df_otm.groupby(['quote_date','expiration'])['delta_otm'].min().to_frame()
        df_otm = pd.merge(df_otm,df_min,on=['quote_date','expiration','delta_otm']).drop_duplicates(subset=['quote_date'])
        df_otm = df_otm[['expiration','enter']]
        df = pd.merge(df_atm,df_otm,on='expiration').rename(columns={'enter_x':'atm','enter_y':'otm'})
        save(df)
    # elif code_part == 3:
        #df = pd.read_csv('../devel/df2.csv')
        """
        df0 = df.loc[df['days_to_exp'] == 0].rename(columns={'enter':'atm0'}).drop(columns=['days_to_exp'])
        df1 = df.loc[df['days_to_exp'] == 1].rename(columns={'enter':'atm1'})
        df2 = df.loc[df['days_to_exp'] == 2].rename(columns={'enter':'atm2'})
        df3 = df.loc[df['days_to_exp'] == 3].rename(columns={'enter':'atm3'})
        df4 = df.loc[df['days_to_exp'] == 4].rename(columns={'enter':'atm4'})
        df = pd.merge(df0,df1[['atm1','expiration']],on=['expiration'])
        df = pd.merge(df,df2[['atm2','expiration']],on=['expiration'])
        df = pd.merge(df,df3[['atm3','expiration']],on=['expiration'])
        df = pd.merge(df,df4[['atm4','expiration']],on=['expiration'])
        df = df[['expiration','atm0','atm1','atm2','atm3','atm4','underlying']]
        save(df)
        """
    if code_part in [0,4]:
        df = pd.read_csv('../devel/df.csv')
        df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
        df = df.loc[df['expiration']>bd][['expiration','atm','otm','underlying']]
        df = scale_stock(df)
        df = df.set_index('expiration')
        df = df[plot]
        ax = df.plot(figsize=(11, 7))
        freq = 'M' if len(df) > 10 else 'D'
        xtick = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
        ax.set_xticks(xtick, minor=False)  # play with parameter
        ax.grid('on', which='minor')
        ax.grid('on', which='major')
        plt.savefig('../devel/%s.png' % openf)
        plt.show()


if __name__ == '__main__':
    ticker = read_entry('research','ticker')
    ent_weekday = int(read_entry('research','enter_weekday'))
    exp_in = int(read_entry('research','expires_in'))
    show_r = int(read_entry('research','show_rows'))
    year = read_entry('research','year')
    arg = read_entry('research','arg')
    arg_sort = 'prc_c'
    atm_price()
    # max_move(tick=ticker,enter_weekday=ent_weekday,show_rows=show_r,yr=year,sort=arg_sort)
    # lowest_week_price(tick=ticker,enter_weekday=ent_weekday,show_rows=show_r,arg=arg,yr=year)
    # single_opt(opt_date='2020-03-20',strike=177)
