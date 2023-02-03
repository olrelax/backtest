from datetime import datetime,timedelta
from dateutil.relativedelta import *
import pandas as pd
from os import path
import time
from configparser import ConfigParser, NoOptionError

def days_from_to(d0,d1):
    delta = d1 - d0
    return delta.days
def read_opt_file(ofn):
    df = pd.read_csv(ofn)
    df['quote_date'] = pd.to_datetime(df['quote_date'], format='%Y-%m-%d')
    df['expiration'] = pd.to_datetime(df['expiration'], format='%Y-%m-%d')
    return df
def scale_stock(df):
    stock = 'Close'
    if 'opt_sum_1' in df.columns:
        cols = ['opt_sum_0', 'opt_sum_1', 'opt_sum']
    else:
        cols = ['opt_sum_0', 'opt_sum']
    opt_min = df[cols].to_numpy().min()
    opt_max = df[cols].to_numpy().max()
    under_min = df[stock].to_numpy().min()
    under_max = df[stock].to_numpy().max()
    df[stock] = df[stock] * (opt_max - opt_min) / (under_max - under_min)
    under_min = df[stock].to_numpy().min()
    df[stock] = df[stock] - under_min + opt_min
    return df


def fl(arg):
    string = path.basename(arg.filename) + ':' + str(arg.lineno) + ' ' + datetime.now().strftime('%M:%S:%f')
    print(string)

def read_opt(ticker,year,opt_type):
    fn = '../data/%s/%s_CBOE_%d_%s.csv' % (ticker,ticker,year,opt_type)
    try:
        opts = pd.read_csv(fn, index_col=0)
        opts['quote_date'] = pd.to_datetime(opts['quote_date'], format='%Y-%m-%d')
        opts['expiration'] = pd.to_datetime(opts['expiration'], format='%Y-%m-%d')
    except FileNotFoundError:
        prn('No such file %s' % fn,'blue')
        return None
    return opts

def ts(date=datetime.now()):
    return time.mktime(date.timetuple())



def d2s(dtm,fmt='%Y-%m-%d'):
    return datetime.strftime(dtm,fmt)

def s2d(text,fmt='%Y-%m-%d'):
    try:
        s = datetime.strptime(text,fmt)
    except Exception as e:
        prn('s2d error:','red')
        s = '{}'.format(e)
        exit(s)
    return s

dtm_fmt_Y_m_d = '%Y-%m-%d'
def prn(text, color=''):
    if color == 'red':
        print('\033[31m' + text + '\033[0m')
    elif color == 'green':
        print('\033[32m' + text + '\033[0m')
    elif color == 'yellow':
        print('\033[33m' + text + '\033[0m')
    elif color == 'blue':
        print('\033[34m' + text + '\033[0m')
    elif color == 'magenta':
        print('\033[35' + text + '\033[0m')
    elif color == 'cyan':
        print('\033[36m' + text + '\033[0m')
    elif color == 'white':
        print('\033[37m' + text + '\033[0m')
    else:
        print(text)




def get_closest(df_arg, val, put_or_call):
    min_delta, premium, strike = 1000000., 0., 0
    df = df_arg.loc[df_arg['option_type'] == put_or_call]
    for index, row in df.iterrows():
        row_val = row['strike']
        delta = abs(row_val - val)
        if delta < min_delta:
            min_delta = delta
            strike = row_val
            premium = row['option_price']
    return strike, premium

def last_month_day(current_date):
    next_month_date = current_date.replace(day=28) + timedelta(days=4)
    return next_month_date - timedelta(days=next_month_date.day)


def add_days(dt, n):
    return dt + relativedelta(days=n)


def add_work_days(from_date, n):
    business_days_to_add = n
    current_date = from_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5:  # sunday = 6
            continue
        business_days_to_add -= 1
    return current_date


def add_weeks(dt,n):
    return dt + relativedelta(weeks=n)
def add_months(dt,n):
    return dt + relativedelta(months=n)



def save_csv(df,fn):
    df.to_csv(fn, index=False)


parser = None

#def set_config_object():
#    global config_object
#    config_object = ConfigParser()
#    config_object.read('data/init/config.ini')


def read_entry(section, entry_name):
    global parser
    if parser is None:
        parser = ConfigParser()
        parser.read('config.ini')
    a = parser.get(section, entry_name)
    return a
def flt(ch):
    return float(ch) if len(ch)>0 else 0.0

