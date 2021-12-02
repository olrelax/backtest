import pandas as pd
from datetime import datetime,timedelta
from dateutil.relativedelta import *
from au import get_opt
date_fmt = '%Y.%m.%d'
opts = pd.read_csv('../data/SPY_CBOE_2020_PUT.csv', index_col=0)
opts['quote_date'] = pd.to_datetime(opts['quote_date'],format='%Y-%m-%d')
opts['expiration'] = pd.to_datetime(opts['expiration'],format='%Y-%m-%d')
stock = pd.read_csv('../data/SPY.csv',names=['date','o','h','l','c','f1','f2','f3'],delimiter='\t')
stock['date'] = pd.to_datetime(stock['date'],format=date_fmt)
start_date = datetime.strptime('2020.01.01',date_fmt)
stock = stock[stock['date'] > start_date].copy().reset_index(drop=True)
class Portfolio:
    stock = 0
    lp_strike = 0
    lp_premium = 0     # long put enter price
    enter_price = 0     # stock enter price
    enter_date = datetime.strptime('2019.12.31',date_fmt)
    expiration = datetime.strptime('2019.12.31',date_fmt)
    unrealized = 0
    realized = 0

    def enter(self,enter_date,enter_price,expiration,lp_premium,lp_strike):
        self.stock = 1
        self.lp_strike = lp_strike
        self.expiration = expiration
        self.enter_date = enter_date
        self.enter_price = enter_price
        self.lp_premium = lp_premium
        return 0

    def unrealised_pl(self, dt, stock_price,lp_price):
        stock_pl = stock_price - self.enter_price
        lp_pl = lp_price - self.lp_premium
        if self.expiration == dt:
            self.lp_strike = 0
        return stock_pl + lp_pl

p = Portfolio()
a_month = relativedelta(months=1)
for i, r in stock.iterrows():
    if i == 0:
        date = r['date']
        # exp = date + timedelta(days=7)
        exp = date + a_month
        ret_code, opt = get_opt(opts,date,exp,r['c'],'P')
        print(ret_code,opt)
        exit()
        #  p.enter(r['quote_date'],r[i])

print(get_opt(opts,'2020-01-10','2020-02-10',327,'P'))
exit()

#res = get_opt(opts,'2020-01-08','2020-01-15',1318.6,'P','strike')
#print(res)

