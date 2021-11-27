import pandas as pd
import matplotlib.pyplot as plt


short_shift = -8
long_shift = -1
commission = 2.1
summary = 0
trade_num = 0
if short_shift >= long_shift:
    if long_shift > 0:
        exit('wrong shift values')
if long_shift < -1:
    exit('long_shift cannot be < -1.')
if long_shift <= 0 < short_shift:
    exit('wrong shift values')


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


def bp(doit):
    if doit:
        print('breakpoint')




cd = ''
h, m, low, skp = 0, 0, 0, 0
for i, r in src_df.iterrows():
    d = r['data_date']
    if not d == cd:
        cd = d
        do_trade_date(cd)

dfr = result_df[['trade_date', 'expiry_price', 'spread_result', 'summary']]
dfr.to_csv('tmp/t.csv', date_format='%Y-%m-%d', index=False)
dfr = pd.read_csv('tmp/t.csv', index_col=0)
ax = dfr.plot(figsize=(10, 8), subplots=True)
y_min, y_max = ax[1].get_ylim()
ax[1].text(0, y_max * 0.5, 'h %d, m% d, l %d, skip %d p&l = %.2f' % (h, m, low, skp, summary))
plt.show()
result_df.to_csv('out/trade(short%d_long%d).csv' % (short_shift, long_shift))
