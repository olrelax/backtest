import pandas as pd
import globalvars as gv
from au import prn,add_days,s2d
def select_expiration(df_a, quote_date,target_expiration,exp_mode_search,opt_type):

    qd = quote_date
    exp = target_expiration
    if exp_mode_search not in ('closest','exact'):
        prn('wrong exp_mode_search','red')
        return None
    df_type = df_a.loc[df_a['option_type'] == opt_type]
    if len(df_type) == 0:
        return None
    df_date = df_type.loc[df_type['quote_date'] == qd]
    if len(df_date) == 0:
        return None
    if exp_mode_search == 'closest':    # not exact expiration date
        df_exp = df_date.iloc[(df_date['expiration'] - exp).abs().argsort()]   # exact, before and after dates
        if len(df_exp) > 0:
            exp = df_exp['expiration'].iloc[0]
        else:
            return None
    df_exp = df_date.loc[df_date['expiration'] == exp]
    if len(df_exp) == 0:
        return None
    return pd.DataFrame(df_exp)

def get_atm(df):
    underlying = df['underlying_ask_1545'].iloc[0]
    df_strikes = df.loc[df['strike'] < underlying]
    df_atm = df_strikes.iloc[df_strikes['strike'].argsort()]
    atm_row = df_atm[['open','bid_1545']].iloc[-1]
    return atm_row


def select_opt(df_a, quote_date,target_expiration,search_value,exp_mode_search,search_mode,opt_type,is_short):
    check_exp = target_expiration
    df_exp = select_expiration(df_a, quote_date, check_exp, exp_mode_search, opt_type)
    if df_exp is None:
        if exp_mode_search == 'exact' and quote_date == target_expiration:
            return -22, None,0,0
        return 0, None, 0,0
    atm_row = None
    # if gv.algo is not 'distance':
    df_qd_on_exp = df_a.loc[df_a['quote_date'] == df_exp['expiration'].iloc[0]]
    i = 0
    while len(df_qd_on_exp) == 0:
        check_exp = add_days(check_exp,1)
        df_exp = select_expiration(df_a, quote_date,check_exp,exp_mode_search,opt_type)
        df_qd_on_exp = df_a.loc[df_a['quote_date'] == df_exp['expiration'].iloc[0]]
        i += 1
        if i > 2:
            return 0, None, 0,0
    right_strike = df_qd_on_exp['underlying_ask_1545'].iloc[0]
    stock = df_exp['underlying_ask_1545'].iloc[0]
    sign = -1 if opt_type == 'P' else 1 if opt_type == 'C' else None
    if gv.get_atm:
        atm_row = get_atm(df_exp)
    if search_mode == 'exact_strike':
        df = df_exp.loc[df_exp['strike'] == search_value]
        if len(df) == 0:
            return -18, None, 0,0
    elif search_mode == 'distance':
        if gv.abs_not_percent:
            strike_estimate = stock + sign * search_value
        else:
            strike_estimate = stock * (1 + sign * search_value / 100)
        df = df_exp.iloc[(df_exp['strike'] - strike_estimate).abs().argsort()][0:1]
        if len(df) == 0:
            return -16, None, 0,0
    elif search_mode == 'hedge_distance':
        strike_estimate = search_value
        df = df_exp.iloc[(df_exp['strike'] - strike_estimate).abs().argsort()][0:1]
    elif search_mode in ('nn','base_on_atm','fixprice'):
        df_exp = df_exp[['quote_date','expiration','strike','ask_1545','bid_1545','underlying_ask_1545','underlying_bid_1545']]
        underlying = df_exp['underlying_ask_1545'].iloc[0]
        df_strikes = df_exp.loc[df_exp['strike'] < underlying]
        if search_mode in ('nn','fixprice'):
            opt_price = search_value
        elif search_mode == 'base_on_atm':
            opt_price = atm_row['bid_1545'] * search_value
        else:
            opt_price = -1    # wired value
        df_premium = df_strikes.iloc[(df_strikes['bid_1545'] - opt_price).abs().argsort()] if is_short else df_strikes.iloc[(df_strikes['ask_1545'] - opt_price).abs().argsort()]
        df_closest_premium = df_premium.loc[df_premium['bid_1545'] == df_premium['bid_1545'].iloc[0]] if is_short else df_premium.loc[df_premium['ask_1545'] == df_premium['ask_1545'].iloc[0]]
        df = df_closest_premium.iloc[df_closest_premium['strike'].argsort()]
        if (opt_type == 'P' and not is_short) or (opt_type == 'C' and is_short):
            df = df.iloc[::-1]   # reverse
        if len(df) == 0:
            return -15, None, 0,0
    else:
        return -14, None, 0
    return 0, df.iloc[0], atm_row, right_strike