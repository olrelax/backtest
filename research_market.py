import pandas as pd
from dateutil.relativedelta import *
import mplfinance as mpf
import inspect
from au import *
def add_days(dt):
    return dt + relativedelta(days=7)
days_to_add = 5

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
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
def add_wd(dt):
    return add_work_days(dt,days_to_add)

def max_week_move(tick,expire_in=4,enter_weekday=1,show_rows=5):
    global days_to_add
    days_to_add = expire_in
    df = pd.read_csv('../data/%s-yahoo.csv' % tick)
    df['Date'] = pd.to_datetime(df['Date'])
    df['wkd'] = pd.Series(map(lambda x: x.isoweekday(), df['Date']))     # isoweekday returns 1 for monday
    df['late'] = pd.Series(map(add_wd,df['Date']))
    df_left = df[['Date','Close','wkd','late']]
    df_right = df[['Date','Close','wkd']]
    df1 = pd.merge(df_left,df_right,left_on='late',right_on='Date')
    df1 = df1.loc[df1['wkd_x'] == enter_weekday]

    df1['delta'] = df1['Close_x'] - df1['Close_y']
    df1 = df1.loc[df1.Date_x > s2d('2009-05-04')].reset_index(drop=True)
    df1['wkd_x'] = pd.Series(map(str,df1['wkd_x']))
    df1['wkd_y'] = pd.Series(map(str,df1['wkd_y']))
    df1['wkd'] = df1['wkd_x'] + df1['wkd_y']
    df1['delta_prc'] = 100*(df1['delta'])/df1['Close_x']
    df1 = df1[['Date_x','Close_x','Date_y','Close_y','wkd','delta','delta_prc']]
    down = df1.iloc[df1['delta_prc'].argsort()][-show_rows:]
    up = (df1.iloc[df1['delta_prc'].argsort()][:show_rows])
    up['delta'] = (up['delta'] * -1)
    up['delta_prc'] = (up['delta_prc'] * -1)
    up = up.sort_values('delta')
    # print('-------------------- UP ----------------------------\n',up)
    print('-------------------- DOWN --------------------------\n',down)

if __name__ == '__main__':
    max_week_move(tick='QQQ',expire_in=4,enter_weekday=1,show_rows=10)
