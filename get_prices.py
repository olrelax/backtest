from datetime import datetime, timedelta
from Models import SymbolModel, OptionModel
import pandas as pd
def add_day(inp,days_to_add=1,fmt=None):
    sec_to_add = 86400 * days_to_add
    new_date = inp + timedelta(seconds=sec_to_add)
    if fmt is not None:
        new_date = new_date.strftime(fmt)  # into account such as weekends, vacations, etc.,
    return new_date

sym_name = 'SPY'
symbol_db = SymbolModel.select().where((SymbolModel.symbol == sym_name) & (SymbolModel.data_source == "Tradier")).get()
result_df = None
stock_peewee = OptionModel.get_historic_stock_prices(symbol_db)
stock_df = pd.DataFrame(list(stock_peewee.dicts()))
stock_df.to_csv('out/%s-stock.csv' % sym_name)
exit()
def get_chain_for_date(trade_date, exp_date):
    global result_df
    expiry_pewee = OptionModel.check_expiry_exists(symbol_db, trade_date,exp_date)
    if expiry_pewee.count() > 0:
        expiry_date = expiry_pewee[0].expiration_date
        if not exp_date == expiry_date: exit('err 2')
        options_chain = OptionModel.get_historic_options_chain(symbol_db, trade_date, expiry_date)
        df = pd.DataFrame(list(options_chain.dicts()))
        expiry_price_peewee = OptionModel.get_expiry_price(symbol_db,  expiry_date)
        expiry_price = expiry_price_peewee[0].underlying_price
        df['vega'] = expiry_price   # rename the field later
        if result_df is None:
            result_df = df
        else:
            result_df = pd.concat([result_df, df],ignore_index=True)
    else:
        print('No data for %s' % trade_date)

def increment(start, expire_time):
    trade_date = start
    while True:
        expire_date = add_day(trade_date,expire_time)
        get_chain_for_date(trade_date,expire_date)
        trade_date = add_day(trade_date,7)
        if trade_date == datetime(2019, 2, 11):
            print('Finish')
            break

start_trade_date = datetime(2013, 1, 14)
# start_trade_date = datetime(2018, 1, 15)

increment(start_trade_date,expire_time=4)
res = pd.DataFrame(result_df).drop(columns=['symbol','ask_price','ask_size','bid_price','bid_size','delta','gamma','implied_volatility','open_interest','rho']).rename(columns={'last_price': 'option_price','vega': 'expiry_price'})
res.to_csv('out/%s-chains.csv' % sym_name)
