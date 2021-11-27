import pandas as pd
import matplotlib.pyplot as plt
from hedged_short_put import do_hedged_short_put


src_df = pd.read_csv('../data/SPY-chains.csv').drop('Unnamed: 0', axis=1)
result_df = pd.DataFrame(columns=('trade_date', 'underlying_price', 'expiry_price', 'strike_short', 'premium_short',
                                  'strike_long', 'premium_long', 'spread_result', 'total','case','short_depth',
                                  'long_depth','margin','net_premium','commission'))


short_shift = 12
long_shift = 15
if short_shift >= long_shift:
    if long_shift > 0:
        exit('wrong shift values')
if long_shift < -1:
    exit('long_shift cannot be < -1.')
if long_shift <= 0 < short_shift:
    exit('wrong shift values')




total = 0
#h, m, low, skp = 0, 0, 0, 0

cd = ''
n = 0
for i, r in src_df.iterrows():
    d = r['data_date']
    if d == cd:
        continue
    cd = d
    rw,total = do_hedged_short_put(src_df, cd,short_shift,long_shift,total)
    result_df.loc[n] = rw
    n += 1

dfr = result_df[['trade_date', 'expiry_price', 'spread_result','total']]
dfr.to_csv('../tmp/t.csv', date_format='%Y-%m-%d', index=False)
dfr = pd.read_csv('../tmp/t.csv', index_col=0)
ax = dfr.plot(figsize=(10, 8), subplots=True)
y_min, y_max = ax[1].get_ylim()
# ax[1].text(0, y_max * 0.5,)
plt.show()
result_df.to_csv('../out/trade(short%d_long%d).csv' % (short_shift, long_shift))
