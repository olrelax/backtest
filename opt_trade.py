import pandas as pd
import matplotlib.pyplot as plt
from strategies import short_call, long_put

src_df = pd.read_csv('../data/SPY-chains.csv').drop('Unnamed: 0', axis=1)
result_format = pd.DataFrame(columns=('trade_date', 'underlying_price', 'expiry_price', 'call_strike', 'call_premium',
                                      'put_strike', 'put_premium', 'commission', 'call p/l', 'put p/l', 'stock p/l', 'total','aux'))
#add_df = pd.DataFrame(result_format)
add_df = result_format.copy()


def plot(df, text, chart_name=''):
    dfr = df[['trade_date', 'expiry_price', 'call p/l', 'put p/l', 'stock p/l','total']]
    dfr.to_csv('../tmp/t.csv', date_format='%Y-%m-%d', index=False)
    dfr = pd.read_csv('../tmp/t.csv', index_col=0)
    ax = dfr.plot(figsize=(10, 12), subplots=True,grid=True)
    y_min, y_max = ax[0].get_ylim()
    ax[0].text(0, y_max * 0.9, 'p/l=%s' % text)
    plt.savefig('../out/chart-%s.png' % chart_name)
    plt.show()


def test_strategy(strategy_name, shift, prem_limit=10000):
    df = pd.DataFrame(result_format)
    total = 0
    cd = ''
    for idx, row in src_df.iterrows():
        d = row['data_date']
        if d == cd:
            continue
        cd = d
        rw,result = strategy_name(src_df, cd, shift, prem_limit)
        add_df.loc[0] = rw
        total += result
        add_df.loc[0, 'total'] = total
        df = df.append(add_df,ignore_index=True)
    return df

# 'trade_date', 'underlying_price', 'expiry_price', 'call_strike', 'call_premium',
# 'put_strike', 'put_premium', 'commission', 'call p/l', 'put p/l', 'stock p/l', 'total','aux
short_call_result = test_strategy(short_call, 10)
long_put_result = test_strategy(long_put, 2)
res_df = pd.DataFrame(short_call_result)
res_df['put_strike'] = long_put_result['put_strike']
res_df['put_premium'] = long_put_result['put_premium']
res_df['put p/l'] = long_put_result['put p/l']
res_df['stock p/l'] = 100.0*(res_df['expiry_price'] - res_df['underlying_price'])
totl, i = 0,0
for index, r in res_df.iterrows():
    pl = r['stock p/l'] + r['call p/l'] + r['put p/l']
    totl += pl
    res_df.loc[i,'total'] = totl
    i += 1
plot(res_df,'text','name')

res_df.to_csv('../out/trad.csv')

# for p_step in range(20,250,10):
#    prem = float(p_step)/100.0
#    for step in range(4,10,1):
#        dist_to_strike = float(step)/2.0
#        do_trade(prem, dist_to_strike)
