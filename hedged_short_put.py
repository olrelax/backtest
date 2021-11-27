import pandas as pd
import matplotlib.pyplot as plt
src_df = pd.read_csv('data/SPY-chains.csv').drop('Unnamed: 0', axis=1)
result_df = pd.DataFrame(columns=('trade_date', 'underlying_price', 'expiry_price', 'strike_short', 'premium_short',
                                  'strike_long', 'premium_long', 'spread_result', 'summary', 'case','short_depth',
                                  'long_depth','margin','net_premium','commission'))
def do_hedged_short_put(trade_date):
    global result_df, summary, trade_num, h, m, low, skp
    df_pc = src_df.loc[src_df['data_date'] == trade_date]
    df = df_pc.loc[src_df['type'] == 'put']
    df.to_csv('tmp/%s.csv' % trade_date)
    df0 = df.iloc[0]
    underlying_price = df0['underlying_price']
    expiry_price = df0['expiry_price']
    allow_short_only = False
    short_only_trade = False
    # get strike values
    if short_shift < long_shift < 0:
        strike_long, premium_long = get_closest(df, 0)
        strike_short, premium_short = get_closest(df, strike_long - short_shift)  # short_shift is negative
    elif 0 < short_shift < long_shift:
        strike_long, premium_long = get_closest(df, underlying_price - long_shift)
        strike_short, premium_short = get_closest(df, underlying_price - short_shift)
        if strike_short == strike_long:
            print('Warning, strikes are equal for trade_date %s ' % df0['data_date'])
            if allow_short_only:
                strike_long, premium_long = 0, 0
                short_only_trade = True
                print('go single short')
    elif long_shift == 0:
        strike_short, premium_short = get_closest(df, underlying_price - short_shift)
        strike_long, premium_long = 0, 0
    else:
        strike_short, strike_long, premium_short, premium_long = 0, 0, 0, 0
        exit('unknown strategy')

    # calculating profit
    margin = 0.
    if expiry_price >= strike_short:
        case = 'h'
        h += 1
    elif strike_long < expiry_price < strike_short:
        margin = expiry_price - strike_short
        if short_only_trade or long_shift == 0:
            case = 'l'
            low += 1
        else:
            case = 'm'
            m += 1
    elif expiry_price <= strike_long:
        if short_only_trade:
            margin = strike_short - expiry_price
        else:
            margin = strike_long - strike_short
        case = 'l'
        low += 1
    else:
        case = 'unknown case'
        exit(case)

    if long_shift == 0 or short_only_trade:
        net_premium = 100 * premium_short
        trade_commission = commission
    else:
        net_premium = (100.0 * (premium_short - premium_long))
        trade_commission = 2.0 * commission
    spread_result = (100.0 * margin) + net_premium - trade_commission
    long_depth = underlying_price - strike_long if strike_long > 0 else 0
    if net_premium - trade_commission > 0:
        summary += spread_result
        #  'short_depth', 'long_depth', 'margin', 'net_premium', 'commission'
        rw = [trade_date, underlying_price, expiry_price, strike_short, premium_short, strike_long, premium_long,
              spread_result, summary, case, underlying_price - strike_short, long_depth, margin * 100.0, net_premium, trade_commission]
    else:
        rw = [trade_date, underlying_price, expiry_price, strike_short, premium_short, strike_long, premium_long, 0,
              summary, 'skip',underlying_price - strike_short, long_depth,0,net_premium,trade_commission]
        print('%s premium = %.2f' % (trade_date, net_premium - trade_commission))
    result_df.loc[trade_num] = rw
    trade_num += 1
