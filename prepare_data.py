import pandas as pd
from os import walk
from dateutil.relativedelta import *
from datetime import datetime
from au import read_opt,read_entry
from os import system
import time
import urllib.request
import urllib.error
from io import StringIO
import ssl
import inspect

def process_cboe_source_do(ticker,year, option_type):
    i = 0
    f = []
    d = '../data/%s/%s_%s_CBOE_SRC/' % (ticker,ticker,year)
    for (path, names, filenames) in walk(d):
        f.extend(filenames)
        break
    f.sort()

    rf = None
    exp_time = relativedelta(months=2)
    for fn in f:
        if not fn[-3:] == 'csv':
            continue
        df = pd.read_csv('%s/%s' % (d,fn))
        df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
        df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
        qd = df['quote_date'].iloc[0]
        exp = qd + exp_time
        df = df.loc[df['expiration'] <= exp]
        if len(option_type) == 1:
            df = df.loc[df['option_type'] == option_type]
        if i == 0:
            rf = df.copy()
        else:
            # rf = rf.append(df.copy())
            rf = pd.concat([rf,df.copy()])
        i += 1
    fn = '../data/%s/%s_CBOE_%s_%s.csv' % (ticker,ticker,year,option_type)
    rf.to_csv(fn,index=False)
    print('saved %s' % fn)
def process_cboe_source(ticker,year=None,option_type='P,C'):
    if option_type == 'P,C':
        process_cboe_source_do(ticker,year,'P')
        process_cboe_source_do(ticker,year,'C')
    elif option_type == 'PC':
        process_cboe_source_do(ticker,year,'PC')

def download_yahoo(bd,ticker):

    ed = datetime.today().strftime('%Y-%m-%d')
    b = time.mktime(datetime.strptime(bd, '%Y-%m-%d').timetuple())
    e = time.mktime(datetime.strptime(ed, '%Y-%m-%d').timetuple())
    fn = '../data/%s/%s-yahoo.csv' % (ticker,ticker)
    url = 'https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%d&period2=%d&interval=1d&events=history&includeAdjustedClose=true' % (ticker,b,e)
    print(url)
    try:
        with urllib.request.urlopen(url,context=ssl.SSLContext()) as f:
            html = f.read().decode('utf-8')
    except urllib.error.HTTPError:
        exit('http error: not found')

    string_as_file = StringIO(html)
    # noinspection PyTypeChecker
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

'''def get_sftp_cboe(month=None,days_arg=None):
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
    if count > 1:
        exit("Does not work for count > 1")
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
        localpath = '/Users/oleg/Library/Mobile Documents/com~apple~CloudDocs/PyProjects/Archive/CBOE_SRC/subscriptions/order_000025299/item_000030286/%s' % filename
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
'''
def add_weekday(ticker,y=None,option_type='P,C'):
    if y is None:
        y = 2022

    def add_weekday_do(year, opt_type):
        fn = '../data/%s/%s_CBOE_%s_%s.csv' % (ticker,ticker,year, opt_type)
        print('add weekday %s...' % fn)
        df = pd.read_csv(fn)
        df['quote_date'] = pd.to_datetime(df['quote_date'])
        df['expiration'] = pd.to_datetime(df['expiration'])
        df['weekday'] = pd.Series(map(lambda x: x.isoweekday(), df['quote_date']))
        df['exp_weekday'] = pd.Series(map(lambda x: x.isoweekday(), df['expiration']))
        df['days_to_exp'] = pd.Series(map(td, (df['expiration'] - df['quote_date'])))
        df.to_csv('%s' % fn, index=False)
        print('done wkd %s' % fn)
    if option_type=='P,C':
        add_weekday_do(y,'P')
        add_weekday_do(y, 'C')
    else:
        add_weekday_do(y,'PC')



def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]


def save(dtf,arg_name=None):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    dtf.to_csv('../devel/%s.csv' % name,index=False)

def loc_weekly_exp_cboe(ticker,y,t,exact=True):
    o = read_opt(ticker,y,t)
    if o is None:
        exit()
    o['quote_date'] = pd.to_datetime(o['quote_date'])
    o['expiration'] = pd.to_datetime(o['expiration'])
    d = o[['quote_date','expiration','strike','underlying_bid_1545','underlying_ask_1545','bid_1545','ask_1545','underlying_bid_eod','underlying_ask_eod','bid_eod','ask_eod','weekday','exp_weekday','days_to_exp']]
    # qd8 = d.loc[(d['days_to_exp'] == 0) | (d['days_to_exp'] == 6) | (d['days_to_exp'] == 7) | (d['days_to_exp'] == 8)]
    if exact:
        qd8 = d.loc[((d['days_to_exp'] == 0) | (d['days_to_exp'] == 7)) & ((d['weekday'] == 1) | (d['weekday'] == 3) | (d['weekday'] == 5))]
    else:
        qd8 = d.loc[(d['days_to_exp'] == 0) | (d['days_to_exp'] == 7) | ((d['days_to_exp'] == 6) & d['weekday'] == 2) | ((d['days_to_exp'] == 8) & (d['weekday'] == 1))]

    # select list of expiration dates:
    d_exp = qd8[['expiration']].drop_duplicates(subset=['expiration'])
    # remove expirations for which datafile for date of expiration doesn't exist:
    dm = d_exp.merge(qd8,left_on='expiration',right_on='quote_date').drop(columns='expiration_x').rename(columns={'expiration_y':'expiration'})
    print('%d%s done' % (y,t))
    return dm


def loc_mon_fri(ticker,y,opt_type,wks):
    o = read_opt(ticker,y,opt_type)
    if o is None:
        exit()
    days_to_exp = 4+7*(wks-1)
    d = o[['quote_date','expiration','option_type','strike','underlying_bid_1545','underlying_ask_1545','open','high','low','close','bid_1545','ask_1545','underlying_bid_eod','underlying_ask_eod','bid_eod','ask_eod','weekday','exp_weekday','days_to_exp']].sort_values(['quote_date','expiration','strike','option_type'])
    d = d.loc[((d['days_to_exp'] == 0) & (d['weekday'] == 5)) | ((d['days_to_exp'] == days_to_exp) & (d['weekday'] == 1))]
    print('%s %dw%d weeks done' % (opt_type,y,wks))
    return d

def make_long_file(start_year):
    df_all = None
    now = datetime.now()
    for step in range(now.year - start_year + 1):
        y = start_year + step
        y_opts = read_opt('QQQ',y,'P')
        df_all = y_opts if step == 0 else df_all.append(y_opts,ignore_index=True)
    # df_all['pair_all'] = df_all['quote_date'].astype(str) + df_all['expiration'].astype(str)
    df_all.to_csv('../data/SPY_CBOE_%d-2022_P.csv' % start_year)
def join_stock(df,ticker):
    sfn = '../data/%s/%s-yahoo.csv' % (ticker,ticker)
    ofn = '../data/%s/%s_mon_fri_P.csv' % (ticker,ticker)
    stock = pd.read_csv(sfn,parse_dates=['Date'])[['Date','Open','High','Low','Close']].rename(columns={'Date':'quote_date'})
    opt = pd.read_csv(ofn,parse_dates=['quote_date']) if df is None else df
    df = pd.merge(opt,stock,on='quote_date').rename(columns={'Open':'underlying_open','High':'underlying_high','Low':'underlying_low','Close':'underlying_close'})
    return df
def repair(ticker,opt_type):
    fn = '../data/%s/%s_mon_fri_%s_1.csv' % (ticker,ticker,opt_type)
    df = pd.read_csv(fn)
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df_z = df.loc[df['underlying_bid_eod'] == 0].copy()
    df_z['underlying_bid_eod'] = df_z['underlying_close']
    df_z['underlying_ask_eod'] = df_z['underlying_close']
    df_nz = df.loc[df['underlying_bid_eod'] > 0]
    df = pd.concat([df_nz,df_z],ignore_index=True)
    df = df.sort_values(['quote_date','expiration','strike'])
    df.to_csv(fn,index=False)

def process_data(ch,arg_1=None,arg_2=None,arg_3=None):
    if ch == 'y':
        download_yahoo('2007-01-01',arg_1)
    elif ch == 'r':
        process_cboe_source(ticker=arg_1,year=int(arg_2),option_type=arg_3)   # 'PC' for single file for both types, or 'P,C' for 2 separate files for each type
        add_weekday(ticker=arg_1,y=int(arg_2),option_type=arg_3)
    elif ch == 'mf':
        ticker = arg_1
        start_year = int(arg_2)
        opt_type = arg_3
        fun = loc_mon_fri
        weeks = 1   #

        w = fun(ticker=arg_1,y=start_year,opt_type=opt_type,wks=weeks)
        for i in range(2022 - start_year):
            w = pd.concat([w,fun(ticker=arg_1,y=1+start_year+i,opt_type=opt_type,wks=weeks)],ignore_index=True)
        w = join_stock(w,ticker)
        fn = '../data/%s/%s_mon_fri_%s_%d.csv' % (ticker,ticker,opt_type,weeks)
        # noinspection PyTypeChecker
        w.to_csv(fn,index=False)
    elif ch == 'repair':
        repair(ticker=arg_1,opt_type=arg_3)
def deb():
    d = '../data/SPY_2022_CBOE_SRC/'
    system('ls %s|tail -n 5' % d)


def select_task():
    chars = read_entry('prepare','chars')
    arg1 = read_entry('prepare','arg1')
    arg2 = read_entry('prepare','arg2')
    arg3 = read_entry('prepare','arg3')
    process_data(chars,arg1,arg2,arg3)

if __name__ == '__main__':
    select_task()
