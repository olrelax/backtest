from au import get_closest

commission = 2.1
allow_short_only = True  # can tune
def long_put_short_call(src_df, trade_date, put_shift,call_shift, total,premium_limit):
    df_pc = src_df.loc[src_df['data_date'] == trade_date]
    df_put = df_pc.loc[src_df['type'] == 'put']
    # df_put.to_csv('../tmp/put_%s.csv' % trade_date)
    df_call = df_pc.loc[src_df['type'] == 'call']
    # df_call.to_csv('../tmp/call_%s.csv' % trade_date)
    underlying_price = df_put.iloc[0]['underlying_price']
    expiry_price = df_put.iloc[0]['expiry_price']
    put_strike, put_premium = get_closest(df_put, underlying_price - put_shift,'put')
    call_strike, call_premium = get_closest(df_call, underlying_price + call_shift,'call')
    # put:
    if put_premium < premium_limit:
        put_premium_result = -put_premium * 100.0 - commission
        if expiry_price >= put_strike:   # expire OTM
            put_margin = 0
            case = 'pOTM'
        else:   # expire ITM
            put_margin = 100.0*(put_strike - expiry_price)
            case = 'pITM '
        put_result = put_premium_result + put_margin
    else:
        put_result = 0
        case = 'ps '
    # call:
    call_premium_result = 100.0 * call_premium - commission
    if expiry_price <= call_strike:    # expire OTM
        call_margin = 0
        call_case = case + 'cOTM'
    else:
        call_margin = 100.0*(call_strike - expiry_price)    # expire ITM, negative value
        call_case = case + 'cITM'
    if call_premium_result > 0:
        call_result = call_margin + call_premium_result
        case = case + call_case
    else:
        call_result = 0
    trade_result = put_result + call_result


    total += trade_result
    rw = [trade_date, underlying_price, expiry_price, call_strike, call_premium, put_strike, put_premium,
          trade_result, total, case, 0, 0, 0, 0, commission]
    return rw,total,case


def long_put(src_df, trade_date, long_shift,total,premium_limit):
    df_pc = src_df.loc[src_df['data_date'] == trade_date]
    df = df_pc.loc[src_df['type'] == 'put']
    df.to_csv('../tmp/%s.csv' % trade_date)
    underlying_price = df.iloc[0]['underlying_price']
    expiry_price = df.iloc[0]['expiry_price']
    strike, premium = get_closest(df, underlying_price - long_shift)
    if premium < premium_limit:
        result = -premium * 100.0 - commission
        case = 'h'
        margin = 0
        if expiry_price < strike:
            margin = 100.0*(strike - expiry_price)
            case = 'l'
        result = result + margin
        total += result
    else:
        result = 0
        case = 'skip'
        margin = 0
    rw = [trade_date, underlying_price, expiry_price, 0, 0, strike, premium,
          result, total, case, 0, 0, margin * 100.0, premium, commission]
    return rw,total,case


def hedged_short_put(src_df, trade_date, short_shift, long_shift, total):
    df_pc = src_df.loc[src_df['data_date'] == trade_date]
    df = df_pc.loc[src_df['type'] == 'put']
    df.to_csv('../tmp/%s.csv' % trade_date)
    underlying_price = df.iloc[0]['underlying_price']
    expiry_price = df.iloc[0]['expiry_price']
    short_only_trade = False    # do not touch it
    # get strike values
    if short_shift < long_shift < 0:
        strike_long, premium_long = get_closest(df, 0)
        strike_short, premium_short = get_closest(df, strike_long - short_shift)  # short_shift is negative
    elif 0 < short_shift < long_shift:
        strike_long, premium_long = get_closest(df, underlying_price - long_shift)
        strike_short, premium_short = get_closest(df, underlying_price - short_shift)
        if strike_short == strike_long:
            e_date = df.iloc[0]['data_date']
            if allow_short_only:
                strike_long, premium_long = 0, 0
                short_only_trade = True
                print('go single short at %s' % e_date)
            else:
                print('Warning, strikes are equal for trade_date %s ' % e_date)
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
    elif strike_long < expiry_price < strike_short:
        margin = expiry_price - strike_short
        if short_only_trade or long_shift == 0:
            case = 'l'
        else:
            case = 'm'
    elif expiry_price <= strike_long:
        if short_only_trade:
            margin = strike_short - expiry_price
        else:
            margin = strike_long - strike_short
        case = 'l'
    else:
        case = 'unknown case'
        exit(case)

    if long_shift == 0 or short_only_trade:
        net_premium = 100 * premium_short
        trade_commission = commission
    else:
        net_premium = (100.0 * (premium_short - premium_long))
        trade_commission = 2.0 * commission
    long_depth = underlying_price - strike_long if strike_long > 0 else 0
    if net_premium - trade_commission > 0:
        spread_result = (100.0 * margin) + net_premium - trade_commission
        total += spread_result
        #  'short_depth', 'long_depth', 'margin', 'net_premium', 'commission'
        rw = [trade_date, underlying_price, expiry_price, strike_short, premium_short, strike_long, premium_long,
              spread_result, total, case, underlying_price - strike_short, long_depth, margin * 100.0, net_premium,
              trade_commission]
    else:
        rw = [trade_date, underlying_price, expiry_price, strike_short, premium_short, strike_long, premium_long, 0,
              total, 'skip', underlying_price - strike_short, long_depth, 0, net_premium, trade_commission]
        print('%s premium = %.2f' % (trade_date, net_premium - trade_commission))
    return rw,total,case
