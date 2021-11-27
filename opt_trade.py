import pandas as pd
import matplotlib.pyplot as plt
from strategies import hedged_short_put, long_put


src_df = pd.read_csv('../data/SPY-chains.csv').drop('Unnamed: 0', axis=1)
result_df = pd.DataFrame(columns=('trade_date', 'underlying_price', 'expiry_price', 'strike_short', 'premium_short',
                                  'strike_long', 'premium_long', 'spread_result', 'total','case','short_depth',
                                  'long_depth','margin','net_premium','commission'))


short_shift = 0
long_shift = 5
if short_shift >= long_shift:
    if long_shift > 0:
        exit('wrong shift values')
if long_shift < -1:
    exit('long_shift cannot be < -1.')
if long_shift <= 0 < short_shift:
    exit('wrong shift values')




h, m, low, s = 0, 0, 0, 0
def count_cases(case_letter):
    global h, m, low
    if case_letter == 'h':
        h += 1
    elif case_letter == 'm':
        m += 1
    elif case_letter == 'l':
        low += 1
# max: p=1.30,s=2.00, t=2241.20

max_total = 0
def do_trade(premium, shift):
    global max_total
    total = 0
    cd = ''
    n = 0
    for i, r in src_df.iterrows():
        d = r['data_date']
        if d == cd:
            continue
        cd = d
        rw, total, case = long_put(src_df, cd, shift, total, premium)
        result_df.loc[n] = rw
        count_cases(case)
        n += 1
    # print('p=%.2f,s=%.2f, t=%.2f' % (premium, shift, total))
    if total > max_total:
        max_total = total
        print('max: p=%.2f,s=%.2f, t=%.2f' % (premium, shift, total))
        dfr = result_df[['trade_date', 'expiry_price', 'spread_result','total']]
        dfr.to_csv('../tmp/t.csv', date_format='%Y-%m-%d', index=False)
        dfr = pd.read_csv('../tmp/t.csv', index_col=0)
        ax = dfr.plot(figsize=(10, 8), subplots=True)
        # y_min, y_max = ax[1].get_ylim()
        # ax[1].text(0, y_max * 0.5,'h=%d m=%d l=%d' %(h,m,low))
        plt.savefig('../out/chart-%s-%s.png' % (prem, dist_to_strike))
        #plt.show()
        result_df.to_csv('../out/trade(short%d_long%d).csv' % (prem, dist_to_strike))

# do_trade(1.3, 3)

for p_step in range(20,250,10):
    prem = float(p_step)/100.0
    for step in range(4,10,1):
        dist_to_strike = float(step)/2.0
        do_trade(prem, dist_to_strike)

