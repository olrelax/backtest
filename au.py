from datetime import datetime,timedelta
from dateutil.relativedelta import *
import pandas as pd
import globalvars as gv
from os import path
import time
"""
from inspect import currentframe, getframeinfo
fl(getframeinfo(currentframe()))
from au import fl
"""
def get_latest_trade_day(date):
    if date is None:
        return gv.stock['date'].iloc[-1]
    else:
        return gv.stock.loc[gv.stock['date'] <= s2d(date)]['date'].iloc[-1]

def get_monthly_opts(date, opts,opt_type):
    possible_exp = add_days(last_month_day(date), max(gv.days2exp_1,gv.days2exp_2) + 5)
    if opt_type == 'C':
        if opts is None:
            gv.opts_annual_C = read_opt(date.year,date,opt_type)
            opts = gv.opts_annual_C.loc[gv.opts_annual_C['quote_date'] >= date].loc[gv.opts_annual_C['quote_date'] <= possible_exp]
        elif date.month > opts['quote_date'].iloc[0].month or date.year > opts['quote_date'].iloc[0].year:
            if date.year == opts['quote_date'].iloc[0].year:
                opts = gv.opts_annual_C.loc[gv.opts_annual_C['quote_date'] >= date].loc[gv.opts_annual_C['quote_date'] <= possible_exp]
            else:
                if gv.opts_annual_next_year_C['quote_date'].iloc[0].year == date.year:
                    gv.opts_annual_C = gv.opts_annual_next_year_C
                else:
                    exit('hm...')
                opts = gv.opts_annual_C.loc[gv.opts_annual_C['quote_date'] >= date].loc[gv.opts_annual_C['quote_date'] <= possible_exp]
        else:
            return opts
        if possible_exp.year > opts['quote_date'].iloc[-1].year:
            gv.opts_annual_next_year_C = read_opt(possible_exp.year,date,opt_type)
            if gv.opts_annual_next_year_C is not None:
                opts = opts.append(gv.opts_annual_next_year_C.loc[gv.opts_annual_next_year_C['quote_date'] <= possible_exp], ignore_index=True)
        return opts
    else:
        if opts is None:
            gv.opts_annual_P = read_opt(date.year,date,opt_type)
            opts = gv.opts_annual_P.loc[gv.opts_annual_P['quote_date'] >= date].loc[gv.opts_annual_P['quote_date'] <= possible_exp]
        elif date.month > opts['quote_date'].iloc[0].month or date.year > opts['quote_date'].iloc[0].year:
            if date.year == opts['quote_date'].iloc[0].year:
                opts = gv.opts_annual_P.loc[gv.opts_annual_P['quote_date'] >= date].loc[gv.opts_annual_P['quote_date'] <= possible_exp]
            else:
                if gv.opts_annual_next_year_P['quote_date'].iloc[0].year == date.year:
                    gv.opts_annual_P = gv.opts_annual_next_year_P
                else:
                    exit('hm...')
                opts = gv.opts_annual_P.loc[gv.opts_annual_P['quote_date'] >= date].loc[gv.opts_annual_P['quote_date'] <= possible_exp]
        else:
            return opts
        if possible_exp.year > opts['quote_date'].iloc[-1].year:
            gv.opts_annual_next_year_P = read_opt(possible_exp.year,date,opt_type)
            if gv.opts_annual_next_year_P is not None:
                opts = opts.append(gv.opts_annual_next_year_P.loc[gv.opts_annual_next_year_P['quote_date'] <= possible_exp], ignore_index=True)
        return opts


def fl(arg):
    string = path.basename(arg.filename) + ':' + str(arg.lineno) + ' ' + datetime.now().strftime('%M:%S:%f')
    print(string)
def read_stock():
    print('read stock hist...')
    stock = pd.read_csv('../data/spy.csv')
    stock['date'] = pd.to_datetime(stock['date'])
    start_date = add_months(s2d(gv.bd),-1)
    stock_1 = stock[stock['date'] >= start_date]
    stock = stock_1[stock_1['date'] >= start_date].copy().reset_index(drop=True)
    return stock

last_year = 3200
def read_opt(year,date,opt_type):
    global last_year
    if year > last_year:
        return None
    print('%s: read options hist %d ...' % (d2s(date),year))
    fn = '../data/SPY_CBOE_%d_%s.csv' % (year,opt_type)
    try:
        opts = pd.read_csv(fn, index_col=0)
    except FileNotFoundError:
        prn('No such file %s' % fn,'blue')
        last_year = year
        return None
    opts['quote_date'] = pd.to_datetime(opts['quote_date'], format='%Y-%m-%d')
    opts['expiration'] = pd.to_datetime(opts['expiration'], format='%Y-%m-%d')
    print('done')
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
def intraday_tested_dates(dt):
    date = d2s(dt)
    dates_list = gv.intraday_tested.split(',')
    return date in dates_list

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


#        else:
#            s_sort = df_bk.iloc[(df_bk['strike'] - target_strike).abs().argsort()]
#            mi = s_sort['strike'].iloc[-1]
#            ma = s_sort['strike'].iloc[0]
#            s = '%s get_opt: looking for strike %.2f at exp %s found %.2f-%.2f' % (d2s(quote_date), target_strike,d2s(expiration), mi,ma)
#            prn(s,'red')
#            return -15, None


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

