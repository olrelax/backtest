import pandas as pd
from datetime import datetime,timedelta
from dateutil.relativedelta import *
from au import get_opt,prn,d2s, s2d
import os
from inspect import currentframe, getframeinfo

opts = pd.read_csv('../data/SPY_CBOE_2020_PUT.csv', index_col=0)
opts['quote_date'] = pd.to_datetime(opts['quote_date'],format='%Y-%m-%d')
opts['expiration'] = pd.to_datetime(opts['expiration'],format='%Y-%m-%d')
stock = pd.read_csv('../data/SPY.csv',names=['date','o','h','l','c','f1','f2','f3'],delimiter='\t')
stock['date'] = pd.to_datetime(stock['date'],format='%Y.%m.%d')
start_date = datetime.strptime('2020.01.01','%Y.%m.%d')
stock = stock[stock['date'] > start_date].copy().reset_index(drop=True)


epoc_start = datetime.strptime('1900-01-01','%Y-%m-%d')
def fl(arg, printit=False):
    string = os.path.basename(arg.filename) + ':' + str(arg.lineno) + ' ' + datetime.now().strftime('%M:%S:%f')
    if printit:
        print(string)
    return string

class Portfolio:
    stock = 0
    lp_strike = 0.
    lp_enter_price = 0.     # long put enter price
    enter_price = 0.     # stock enter price
    enter_date = epoc_start
    expiration = epoc_start
    current_price = 0.0
    realized = 0.

    def enter(self,enter_date,enter_price):
        if self.stock == 0:
            self.stock = 1
            self.enter_date = enter_date
            self.enter_price, self.current_price = enter_price, enter_price
            self.realized = self.realized - 0.021

    def buy_opt(self, expiration, lp_premium, lp_strike):
        if self.lp_strike > 0:
            exit('error 007')
        self.lp_strike = lp_strike
        self.expiration = expiration
        self.lp_enter_price = lp_premium
        self.realized = self.realized - 0.021

    def state(self,date):
        c_date = d2s(date)
        exp_str = d2s(self.expiration)
        ent_str = d2s(self.enter_date)
        s = 'state %s: enter date %s\n'\
            'enter price %.2f\n'\
            'exp %s\n'\
            'strike %.1f\n'\
            'lp_premium %.2f\n'\
            'realized %.2f'\
            % (c_date,ent_str,self.enter_price, exp_str,self.lp_strike,self.lp_enter_price,self.realized)
        print(s)


    def close_opt(self, dt, curr_opt_price,early=False):
        if not early and not dt == self.expiration:
            exit('error 004')
        self.realized += curr_opt_price - self.lp_enter_price
        self.lp_strike = 0
        self.lp_enter_price = 0
        self.expiration = epoc_start


    def current_value(self, dt, stock_price,lp_price):
        if self.lp_strike > 0 and dt > self.expiration:
            exit('Expiration %s missed, today is %s. error 001' % (d2s(self.expiration),d2s(dt)))
        stock_pl = stock_price - self.enter_price
        lp_pl = lp_price - self.lp_enter_price
        return stock_pl, lp_pl, self.realized






p = Portfolio()
a_month = relativedelta(months=1)
def add_days(dt, days):
    return dt + timedelta(days=days)

def get_current_portfolio(date, o):
    opt_price = o['bid_1545']
    stock_price = o['underlying_bid_1545']
    strike = o['strike']
    exp = o['expiration']
    stock_pl, opt_pl, realized = p.current_value(date, stock_price, opt_price)
    total = stock_pl + opt_pl + realized
    return 'date %s, exp %s, strike %.1f, stock %.2f, opt %.2f, stock_pl %.2f, opt_pl %.2f, realized %.2f, total %.2f' \
           % (d2s(date), d2s(exp), strike, stock_price, opt_price, stock_pl, opt_pl, realized, total)

# log = False
# fl(getframeinfo(currentframe()), printit=log)

def trade():
    res = pd.DataFrame({'date':[epoc_start], 'stock_ent':[0.0], 'stock_cur':[0.0], 'exp':[epoc_start],'strike':[0.0],'put_ent':[0.0], 'put_cur':[0.0], 'stock pl':[0.0], 'put pl':[0.0], 'total':[0.0]})
    res['date'] = pd.to_datetime(res['date'])
    res['exp'] = pd.to_datetime(res['exp'])
    row = pd.Series(res.iloc[0])
    for i, r in stock.iterrows():
        date = r['date']
        close = r['c']
        row['date'] = date
        last_trade_day = s2d('2020-12-31')
        first_trade_day = s2d('2020-01-08')
        if date < first_trade_day:
            continue
        if date < p.expiration and date < last_trade_day:
            ret_code, prices_opt = get_opt(opts, date, p.expiration, strike=p.lp_strike, exp_mode_search='exact',strike_round_mode='exact')
            if prices_opt is None:
                exit(ret_code)
            row['stock_cur'] = close
            row['put_cur'] = prices_opt['bid_1545']
        prn('%s' % d2s(date),'blue')
        target_exp = date + a_month
        ret_code, opt = get_opt(opts,date,target_exp,strike=close,exp_mode_search='closest_next',strike_round_mode='down')
        if opt is None:
            exit('%s: opt not found, code %d' % (d2s(date), ret_code))
        underlying_ask_1545 = opt['underlying_ask_1545']
        exp = opt['expiration']
        strike = opt['strike']
        ask_1545 = opt['ask_1545']
        if p.stock == 0:
            p.enter(date,underlying_ask_1545)
            row['stock_ent'] = underlying_ask_1545
        if date == p.expiration:
            ret_code, close_opt = get_opt(opts, date, p.expiration, strike=p.lp_strike, exp_mode_search='exact', strike_round_mode='exact')
            if close_opt is None:
                exit('%s: opt not found, code %d' % (d2s(date),ret_code))
            bid_1545 = close_opt['bid_1545']
            prn('%s: close opt %s %.1f' % (d2s(date),d2s(p.expiration),p.lp_strike),'yellow')
            p.close_opt(date, bid_1545)
            row['put_cur'] = bid_1545
            p.state(date)
            print(get_current_portfolio(date,opt))

        if p.lp_strike == 0 and p.stock == 1:
            prn('%s: buy opt %s %.1f' % (d2s(date),d2s(exp),strike),'yellow')
            p.buy_opt(exp,ask_1545,strike)
            row['exp'] = exp
            row['put_ent'] = ask_1545
            row['strike'] = strike
            p.state(date)
            print(get_current_portfolio(date,opt))
        if date == last_trade_day:
            ret_code, close_opt = get_opt(opts, date, p.expiration, strike=p.lp_strike, exp_mode_search='exact', strike_round_mode='exact')
            if close_opt is None:
                exit('%s: opt not found, code %d' % (d2s(date),ret_code))
            bid_1545 = close_opt['bid_1545']
            p.close_opt(date,bid_1545,early=True)
            row['put_cur'] = bid_1545
            print(get_current_portfolio(date,opt))
            prn('End','yellow')
            break
        res = res.append(row,ignore_index=True)
    res.drop(axis=0,index=0).reset_index(drop=True).to_csv('res.csv')

trade()


