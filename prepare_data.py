import pandas as pd
from os import walk
from dateutil.relativedelta import *
from datetime import datetime
from au import s2d, d2s,prn,add_days,read_opt
from os import system
import time
import urllib.request
import urllib.error
from io import StringIO
import ssl
import paramiko
import zipfile
import inspect

def process_cboe_source_do(year, option_type):
    i = 0
    f = []
    d = '../data/SPY_%s_CBOE_SRC/' % year
    for (path, names, filenames) in walk(d):
        f.extend(filenames)
        break
    f.sort()

    rf = None
    exp_time = relativedelta(months=1)
    for fn in f:
        if not fn[-3:] == 'csv':
            continue
        df = pd.read_csv('%s/%s' % (d,fn))
        df['expiration'] = pd.to_datetime(df['expiration'])
        df['quote_date'] = pd.to_datetime(df['quote_date'])
        qd = df['quote_date'].iloc[0]
        exp = qd + exp_time
        df = df.loc[df['expiration'] <= exp]
        if len(option_type) == 1:
            df = df.loc[df['option_type'] == option_type]
        if i == 0:
            rf = df.copy()
        else:
            rf = rf.append(df.copy())
        i += 1
    fn = '../data/SPY_CBOE_%s_%s.csv' % (year,option_type)
    rf.reset_index(drop=True).to_csv(fn)
    print('saved %s' % fn)
def process_cboe_source(year=None,option_type=None):
    if year is None and option_type is None:
        process_cboe_source_do(2022,'P')
        process_cboe_source_do(2022,'C')

def debug():
    df = pd.read_csv('../data/SPY_CBOE_2020_P.csv')
    print(df.head())
    print(df.tail())
def download_yahoo(bd,ticker):
    ed = datetime.today().strftime('%Y-%m-%d')
    b = time.mktime(datetime.strptime(bd, '%Y-%m-%d').timetuple())
    e = time.mktime(datetime.strptime(ed, '%Y-%m-%d').timetuple())
    fn = '../data/%s-yahoo.csv' % ticker
    url = 'https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%d&period2=%d&interval=1d&events=history&includeAdjustedClose=true' % (ticker,b,e)
    try:
        with urllib.request.urlopen(url,context=ssl.SSLContext()) as f:
            html = f.read().decode('utf-8')
    except urllib.error.HTTPError:
        exit('http error: not found')

    string_as_file = StringIO(html)
    arr = pd.read_csv(string_as_file)
    # SPY = arr.rename(columns={'Date':'date', 'Open':'o', 'High':'h', 'Low':'l', 'Close':'c', 'Adj Close':'vlt', 'Volume':'underlying_bid_1545'})
    arr.to_csv(fn, index=False)
    print(arr.tail())

def intraday(date,bottom=None,top=None):
    path = '../data/intraday'
    fn = '%s/UnderlyingOptionsIntervals_60sec_oi_level2_%s.csv' % (path, date)
    df = pd.read_csv(fn)
    df['expiration'] = pd.to_datetime(df['expiration'])
    if bottom and top:
        df = df.loc[df['option_type'] == 'P'].loc[df['strike'] < top].loc[df['strike'] > bottom].loc[df['expiration'] == date]
    else:
        df = df.loc[df['option_type'] == 'P'].loc[df['expiration'] == date]
    df.to_csv('%s/%s.csv' % (path,date),index=False)
    print(df.info())
def td(d):
    return d.days

def get_sftp_cboe(month=None,days_arg=None):
    days,count,localpath,filename = 0,0,'',''
    if month is None or days_arg is None:
        now = datetime.now()
        yes = add_days(now,-1)
        month = yes.month
        days = [yes.day]
        count = 1
    elif isinstance(days_arg,int):
        days = [days_arg]
        count = 1
    elif isinstance(days_arg,tuple) or isinstance(days_arg,list):
        days = days_arg
        count = len(days)
    if count>1:
        exit("Not works for count>1")
    # filename = 'UnderlyingOptionsEODQuotes_2022-%.2d-%.2d.zip' % (month,day)
    # filepath = 'subscriptions/order_000025299/item_000030286/%s' % filename
    # localpath = '/Users/oleg/Library/Mobile Documents/com~apple~CloudDocs/PyProjects/OptionsBacktest/Archive/CBOE_SRC/subscriptions/order_000025299/item_000030286/%s' % filename
    # paramiko.util.log_to_file("paramiko.log")
    host, port = "sftp.datashop.livevol.com", 22
    d = '../data/SPY_2022_CBOE_SRC/'
    transport = paramiko.Transport((host, port))
    username, password = "olrelax_gmail_com", "Hiwiehi0fz1$"
    print('connect...')
    transport.connect(None, username, password)
    print('connected')
    sftp = paramiko.SFTPClient.from_transport(transport)
    for i in range(count):
        filename = 'UnderlyingOptionsEODQuotes_2022-%.2d-%.2d.zip' % (month,days[i])
        remotepath = 'subscriptions/order_000025299/item_000030286/%s' % filename
        localpath = '/Users/oleg/Library/Mobile Documents/com~apple~CloudDocs/PyProjects/OptionsBacktest/Archive/CBOE_SRC/subscriptions/order_000025299/item_000030286/%s' % filename
        print('get %s->%s' % (remotepath, localpath))
        sftp.get(remotepath, localpath)
        system('ls %s|tail -n 5' % d)
    if sftp:
        print('received')
        sftp.close()
    if transport:
        transport.close()
    with zipfile.ZipFile(localpath, 'r') as zip_ref:
        zip_ref.extractall(d)
    print('ls:')
#    d = '../data/SPY_2022_CBOE_SRC/'
#    system('ls %s | grep %s' % (d,filename[:-4]))
    system('ls %s|tail -n 5' % d)

    print('done')
def add_weekday(y=None):
    if y is None:
        y = 2022

    def add_weekday_do(year, option_type):
        fn = '../data/SPY_CBOE_%s_%s.csv' % (year, option_type)
        df = pd.read_csv('../data/%s' % fn)
        df['quote_date'] = pd.to_datetime(df['quote_date'])
        df['expiration'] = pd.to_datetime(df['expiration'])
        df['weekday'] = pd.Series(map(lambda x: x.isoweekday(), df['quote_date']))
        df['exp_weekday'] = pd.Series(map(lambda x: x.isoweekday(), df['expiration']))
        df['days_to_exp'] = pd.Series(map(td, (df['expiration'] - df['quote_date'])))
        df.to_csv('%s' % fn, index=False)

    add_weekday_do(y,'P')
    add_weekday_do(y, 'C')


def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]


def save(dtf,arg_name=None):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    dtf.to_csv('../out/%s.csv' % name,index=False)

def loc_weekly_exp_spy_cboe(y,t,exact=True):
    o = read_opt(y,t)
    o['quote_date'] = pd.to_datetime(o['quote_date'])
    o['expiration'] = pd.to_datetime(o['expiration'])
    d = o[['quote_date','expiration','strike','underlying_bid_1545','underlying_ask_1545','bid_1545','ask_1545','underlying_bid_eod','underlying_ask_eod','bid_eod','ask_eod','weekday','exp_weekday','days_to_exp']]
    # qd8 = d.loc[(d['days_to_exp'] == 0) | (d['days_to_exp'] == 6) | (d['days_to_exp'] == 7) | (d['days_to_exp'] == 8)]
    if exact:
        qd8 = d.loc[((d['days_to_exp'] == 0) | (d['days_to_exp'] == 7)) & ((d['weekday'] == 1) | (d['weekday'] == 3) | (d['weekday'] == 5))]
    else:
        qd8 = d.loc[(d['days_to_exp'] == 0) | (d['days_to_exp'] == 7) | ((d['days_to_exp'] == 6) & d['weekday'] == 2) | ((d['days_to_exp'] == 8) & (d['weekday'] == 1))]
    d_exp = qd8[['expiration']].drop_duplicates(subset=['expiration'])
    dm = d_exp.merge(qd8,left_on='expiration',right_on='quote_date').drop(columns='expiration_x').rename(columns={'expiration_y':'expiration'})
    print('%d%s done' % (y,t))
    return dm

def make_long_file(start_year):
    df_all = None
    for step in range(2022 - start_year + 1):
        y = start_year + step
        y_opts = read_opt(y,'P')
        df_all = y_opts if step == 0 else df_all.append(y_opts,ignore_index=True)
    # df_all['pair_all'] = df_all['quote_date'].astype(str) + df_all['expiration'].astype(str)
    df_all.to_csv('../data/SPY_CBOE_%d-2022_P.csv' % start_year)

def process_data(ch,arg_1=None,arg_2=None):
    if ch == 'y':
        download_yahoo('2007-01-01','SPY')
    elif ch == 'r':
        process_cboe_source()
        add_weekday()
    elif ch == 'ftp':
        get_sftp_cboe(month=arg_1,days_arg=arg_2)
    elif ch == 'lwe':
        what = 'all_years'
        if what == 'all_years':
            w = loc_weekly_exp_spy_cboe(2018,'P')
            w = w.append(loc_weekly_exp_spy_cboe(2019,'P'),ignore_index=True)
            w = w.append(loc_weekly_exp_spy_cboe(2020,'P'),ignore_index=True)
            w = w.append(loc_weekly_exp_spy_cboe(2021,'P'),ignore_index=True)
            weekly_p = w.append(loc_weekly_exp_spy_cboe(2022,'P'),ignore_index=True)
            weekly_p.to_csv('../data/weekly_P.csv',index=False)
            w = loc_weekly_exp_spy_cboe(2018,'C')
            w = w.append(loc_weekly_exp_spy_cboe(2019,'C'),ignore_index=True)
            w = w.append(loc_weekly_exp_spy_cboe(2020,'C'),ignore_index=True)
            w = w.append(loc_weekly_exp_spy_cboe(2021,'C'),ignore_index=True)
            weekly_c = w.append(loc_weekly_exp_spy_cboe(2022,'C'),ignore_index=True)
            weekly_c.to_csv('../data/weekly_C.csv',index=False)
    elif ch == 'mlf':
        make_long_file(2020)
    elif ch == 'ls':
        deb()
def deb():
    d = '../data/SPY_2022_CBOE_SRC/'
    system('ls %s|tail -n 5' % d)


def select_task():
    process_data('ftp',4,1)

if __name__ == '__main__':
    select_task()
