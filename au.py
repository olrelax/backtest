
def get_closest(df, val, put_or_call='put'):
    min_delta, premium, strike = 1000000., 0., 0
    for index, row in df.iterrows():
        opt_type = row['type']
        if not opt_type == put_or_call:
            continue
        row_val = row['strike_price']
        delta = abs(row_val - val)
        if delta < min_delta:
            min_delta = delta
            strike = row_val
            premium = row['option_price']
    return strike, premium
