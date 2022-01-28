import pandas as pd
import globalvars as gv
from au import prn,add_work_days,s2d
def select_expiration(df_a, quote_date,exp_param,exp_mode,weekday,opt_type):
    qd = quote_date
    df = df_a.loc[df_a['option_type'] == opt_type]
    if len(df) == 0:
        return None
    df = df.loc[df['quote_date'] == qd]
    if len(df) == 0:
        return None
    if exp_mode == 'closest_date':    # not exact expiration date
        est_exp = add_work_days(quote_date,exp_param)
        df = df.loc[df['exp_weekday'] == weekday].loc[df['expiration'] > quote_date]
        if len(df) == 0:
            return None
        df = df.iloc[(df['expiration'] - est_exp).abs().argsort()]   # exact, before and after dates
        if len(df) > 0:
            exp = df['expiration'].iloc[0]
        else:
            return None
    else:
        exp = exp_param
    df_exp = df.loc[df['expiration'] == exp]
    if len(df_exp) == 0:
        return None
    return pd.DataFrame(df_exp)

def get_atm(df):
    underlying = df['underlying_ask_1545'].iloc[0]
    df_strikes = df.loc[df['strike'] < underlying]
    df_atm = df_strikes.iloc[df_strikes['strike'].argsort()]
    atm_row = df_atm[['open','bid_1545']].iloc[-1]
    return atm_row


def select_opt(df_a, quote_date,exp_value,exp_mode,weekday,search_value,value_mode,opt_type,is_short):
    atm_row = None
    df_exp = select_expiration(df_a, quote_date, exp_value, exp_mode, weekday,opt_type)
    if df_exp is None:
        if exp_mode == 'exact_date' and quote_date == exp_value:
            return -22, None,0
        return 0, None, 0
#    df_on_exp = df_a.loc[df_a['quote_date'] == df_exp['expiration'].iloc[0]]
#    i = 0
#    exp_param = exp_value
#    while len(df_on_exp) == 0:
#        exp_param += exp_param
#        df_exp = select_expiration(df_a, quote_date,exp_param,exp_mode,opt_type)
#        df_on_exp = df_a.loc[df_a['quote_date'] == df_exp['expiration'].iloc[0]]
#        i += 1
#        if i > 1:
#            return 0, None, 0,0

#    right_strike = df_on_exp['underlying_ask_1545'].iloc[0]
    stock = df_exp['underlying_ask_1545'].iloc[0]
    sign = -1 if opt_type == 'P' else 1 if opt_type == 'C' else None
    if gv.get_atm or value_mode == 'base_on_atm':
        atm_row = get_atm(df_exp)
    if value_mode == 'exact_strike':
        df = df_exp.loc[df_exp['strike'] == search_value]
    elif value_mode == 'distance':
        if gv.abs_not_percent:
            strike_estimate = stock + sign * search_value
        else:
            strike_estimate = stock * (1 + sign * search_value / 100)
        df = df_exp.iloc[(df_exp['strike'] - strike_estimate).abs().argsort()][0:1]
    elif value_mode == 'hedge_distance':
        strike_estimate = search_value
        df = df_exp.iloc[(df_exp['strike'] - strike_estimate).abs().argsort()][0:1]
    elif value_mode == 'hedge_discount':
        price_estimate = search_value
        df = df_exp.iloc[(df_exp['ask_1545'] - price_estimate).abs().argsort()][0:1]
    elif value_mode in ('nn','base_on_atm','fixprice'):
        df_exp = df_exp[['quote_date','expiration','strike','ask_1545','bid_1545','underlying_ask_1545','underlying_bid_1545']]
        underlying = df_exp['underlying_ask_1545'].iloc[0]
        df_strikes = df_exp.loc[df_exp['strike'] < underlying]
        if value_mode in ('nn','fixprice'):
            target_price = search_value
        elif value_mode == 'base_on_atm':
            target_price = atm_row['bid_1545'] * search_value
        else:
            target_price = -1    # wired value
        field = 'bid_1545' if is_short else 'ask_1545'
        df_premium = df_strikes.iloc[(df_strikes[field] - target_price).abs().argsort()]
        # if there is multiple  strikes for the same premium:
        df_strikes_for_same_premium = df_premium.loc[df_premium[field] == df_premium[field].iloc[0]]
        df = df_strikes_for_same_premium.iloc[df_strikes_for_same_premium['strike'].argsort()]
        if (opt_type == 'P' and not is_short) or (opt_type == 'C' and is_short):
            df = df.iloc[::-1]   # reverse
    else:
        return -2, None
    if len(df) == 0:
        return -1, None
    return 0, df.iloc[0], atm_row
