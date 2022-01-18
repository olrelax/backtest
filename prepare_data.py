import pandas as pd
from os import walk
from dateutil.relativedelta import *
from datetime import datetime,timedelta
from au import s2d, d2s,prn
from os import system
import time
import urllib.request
import urllib.error
from io import StringIO
import ssl




def append_cboe(new_data_fn, option_type='P'):
    if len(option_type) > 1:
        exit('not impl for option_type \'%s\'' % option_type)
    exp_time = relativedelta(months=1)
    old_data_fn = '../data/SPY_CBOE_2021_%s.csv' % option_type
    df0 = pd.read_csv(old_data_fn)
    df1 = pd.read_csv(new_data_fn)
    df1['expiration'] = pd.to_datetime(df1['expiration'])
    df1['quote_date'] = pd.to_datetime(df1['quote_date'])
    df0['expiration'] = pd.to_datetime(df0['expiration'])
    df0['quote_date'] = pd.to_datetime(df0['quote_date'])
    qd = df1['quote_date'].iloc[0]
    exp = qd + exp_time
    df1 = df1.loc[df1['expiration'] <= exp].loc[df1['option_type'] == option_type]
    df = df0.append(df1,ignore_index=True)
    print(df.tail())
    print('saving csv...')
    df.to_csv(old_data_fn,index=False)

def process_cboe_source(year='2022', option_type='P'):
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
def cat():
    df1 = pd.read_csv('../data/SPY_CBOE_2020_P.csv',index_col=0)
    df2 = pd.read_csv('../data/SPY_CBOE_2021_P.csv',index_col=0)

    df1['quote_date'] = pd.to_datetime(df1['quote_date'], format='%Y-%m-%d')
    df1['expiration'] = pd.to_datetime(df1['expiration'], format='%Y-%m-%d')
    df2['quote_date'] = pd.to_datetime(df2['quote_date'], format='%Y-%m-%d')
    df2['expiration'] = pd.to_datetime(df2['expiration'], format='%Y-%m-%d')
    print(df1.head())
    print(df2.tail())


    df = pd.concat([df1,df2],ignore_index=True)
    fn = '../data/SPY_CBOE_%s_%s_P.csv' %('2020','2021')
    df.to_csv(fn,index=False)

def debug():
    df = pd.read_csv('../data/SPY_CBOE_2020_P.csv')
#    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
#    df = df.loc[df['quote_date'] > s2d('2021-01-01')]
#    df.to_csv('../debug/ddf.csv')
    print(df.head())
    print(df.tail())
def cut():
    end = s2d('2020-03-01')
    df = pd.read_csv('../data/SPY_CBOE_2020_2021_P.csv')
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df = df[df['quote_date'] < end]
    df.to_csv('../data/SPY_CBOE_2020_02_P.csv')
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

def make_history_with_opt(start_date):
    spy = pd.read_csv('../data/SPY-yahoo.csv')
    spy = spy.rename(columns={'Date':'date', 'Open':'open', 'High':'high', 'Low':'low', 'Close':'close', 'Adj Close':'volatility', 'Volume':'underlying_bid_1545'})

    spy['underlying_bid_1545'] = 0
    spy['volatility'] = 0
    spy['date'] = pd.to_datetime(spy['date'], format='%Y-%m-%d')
    opt = pd.DataFrame([])
    underlying_bid_1545_idx = spy.columns.get_loc('underlying_bid_1545')
    close_idx = spy.columns.get_loc('close')
    for i, r in spy.iterrows():
        date = r['date']
        if date > s2d(start_date):
            if opt.empty or date.year > opt['quote_date'].iloc[0].year:
                opt = pd.read_csv('../data/SPY_CBOE_%d_P.csv' % date.year)
                opt['quote_date'] = pd.to_datetime(opt['quote_date'], format='%Y-%m-%d')
                print('read %s opt' % d2s(date))

        opt_date = opt.loc[opt['quote_date'] == date] if not opt.empty else pd.DataFrame([])
        if len(opt_date) > 0:
            ua = opt_date['underlying_bid_1545'].iloc[0]
        else:
            ua = spy.iloc[i,close_idx]
        spy.iat[i, underlying_bid_1545_idx] = ua

    a = 'y'
    if a == 'y':
        print('calculate volatility:')
        spy = calc_vlt(spy)
    print('get_prices_from_opt result:')
    print(spy[['date','close','underlying_bid_1545','volatility']].head(3))
    print(spy[['date','close','underlying_bid_1545','volatility']].tail(3))
    return spy

def calc_vlt(obj,w=7):
    if isinstance(obj,str):
        spy = pd.read_csv(obj)
    elif isinstance(obj,pd.DataFrame):
        spy = obj
    else:
        spy = None
        exit('Error calc_vlt')
    spy['volatility'] = 100 * (spy['underlying_bid_1545'].rolling(window=w).max() - spy['underlying_bid_1545']) / spy['underlying_bid_1545'].rolling(
        window=w).max()
    print('calc_vlt result:')
    print(spy[['date','close','volatility']].tail(3))
    return spy

def drop_last_row(path):
    spy = pd.read_csv(path)
    i = len(spy)
    last_date = spy['date'].iloc[-1]
    a = input('drop %s y/[n]' % last_date)
    if a == 'y':
        spy = spy.drop(axis=0, index=i-1).reset_index(drop=True)
        spy.to_csv(path, index=False)
    print('drop_last_row result:')
    print(spy[['date','close','vlt']].tail(3))


def add_new_row_manually(src,date,o,h,low,c):
    spy = pd.read_csv(src)
    spy['date'] = pd.to_datetime(spy['date'], format='%Y-%m-%d')
    if date == 'now':
        date = datetime.now()
    else:
        date = s2d(date)
    row = spy.loc[spy['date'] == date]
    if len(row) > 0:
        prn('Already exists','yellow')
        a = input('Update? y/[n]')
        if not a == 'y':
            exit('exit')
        i = spy.loc[spy['date'] == date].index.to_list()[0]
        spy.iloc[i] = [date,o,h,low,c,0,c,c,0]
    else:
        row = pd.Series(spy.iloc[-1])
        row['date'] = date
        row['open'] = o
        row['high'] = h
        row['low'] = low
        row['close'] = c
        row['underlying_bid_1545'] = c
        row['volatility'] = 0
        spy = spy.append(row, ignore_index=True)
    spy = spy.sort_values('date').reset_index(drop=True)
    print('new_row result:')
    print(spy[['date','c','vlt']].tail(3))
    return spy

def get_vlt(date):
    spy = pd.read_csv('../data/spy.csv')
    today_record = spy.loc[spy['date'] == date]
    if len(today_record) == 0:
        prn('get_vlt: no data for %s' % date,'red')
        return 0,0
    vlt = today_record.iloc[0].loc['vlt']
    stock = today_record.iloc[0].loc['c']
    return vlt,stock

def view(last_row=False):
    spy = pd.read_csv('../data/spy.csv')
    if not last_row:
        spy = spy[['date','o','h','l','c','vlt']]
        print(spy.tail())
    opts = pd.read_csv('../data/SPY_CBOE_2021_P.csv')
    print(opts[['quote_date','expiration','strike']].tail())
def add_from_yahoo(update=False):
    spy = pd.read_csv('../data/spy.csv')
    spy_yahoo = pd.read_csv('../data/SPY-yahoo.csv')
    spy['date'] = pd.to_datetime(spy['date'])
    spy_yahoo['date'] = pd.to_datetime(spy_yahoo['date'])
    spy_yahoo['underlying_bid_1545'] = spy_yahoo['c']
    spy_yahoo['vlt_ask_1545'] = spy_yahoo['vlt']
    last_date = spy.iloc[len(spy) - 1].loc['date']
    new_data = spy_yahoo.loc[spy_yahoo['date'] > last_date]
    if len(new_data) > 0:
        spy = spy.append(new_data,ignore_index=True,)
        print(spy.tail())
        spy.to_csv('../data/spy.csv',index=False)
        print('some rows was added')
    elif not update:
        print('No new data')
    else:
        idx = len(spy_yahoo)-1
        date = spy_yahoo.iloc[len(spy_yahoo)-1,0]
        i = spy.loc[spy['date'] == date].index.to_list()[0]
        ser = spy_yahoo.iloc[idx]
        spy.iloc[i] = ser

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


def process_data(routine='w',arg_1=None,arg_2=None):
    spy_path = '../data/spy.csv'
    for ch in routine:
        if ch == 'h':
            make_history_with_opt('2018-01-01').to_csv(spy_path, index=False)
        elif ch == 'v':
            calc_vlt(spy_path).to_csv(spy_path, index=False)
        elif ch == 'd':
            download_yahoo('2017-01-01','SPY')
        elif ch == 'p':
            drop_last_row(spy_path)
        elif ch == 'w':
            view()
        elif ch == 'r':
            process_cboe_source(year=arg_1,option_type=arg_2)
        elif ch == 'a':
            append_cboe('../data/SPY_2021_CBOE_SRC/UnderlyingOptionsEODQuotes_2021-12-31.csv', option_type='P')
        elif ch == 't':
            cat()
        elif ch == 'y':
            add_from_yahoo(update=True)
        elif ch == 'n':
            add_new_row_manually(spy_path, '2021-12-16', 471.3, 464.86, 469.72, 470.65).to_csv(spy_path, index=False)


# Adding subscription:
# copy new files to main SPY_20YY_CBOE_SRC folder. Do d (yahoo), r (process opt), h (history with opt)
if __name__ == '__main__':
    process_data('h')
    # intraday('2020-02-24')
