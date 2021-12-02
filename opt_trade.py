import pandas as pd
import matplotlib.pyplot as plt
from strategies import short_call, long_put

src_df = pd.read_csv('../data/SPY-chains.csv').drop('Unnamed: 0', axis=1)
result_format = pd.DataFrame(columns=('trade_date', 'underlying_price', 'expiry_price', 'call_strike', 'call_premium',
                                      'put_strike', 'put_premium', 'commission', 'call p/l', 'put p/l', 'stock p/l', 'total','aux'))
add_df = result_format.copy()

def plot(df, text, chart_name=''):
    # dfr = df[['trade_date', 'expiry_price', 'call p/l', 'put p/l', 'stock p/l','total']]
    dfr = df[['trade_date', 'put p/l','aux','stock p/l','total']]
    dfr.to_csv('../tmp/t.csv', date_format='%Y-%m-%d', index=False)
    dfr = pd.read_csv('../tmp/t.csv', index_col=0)
    ax = dfr.plot(figsize=(18, 10), subplots=False,grid=True)
    y_min, y_max = ax.get_ylim()
    ax.text(0, y_max * 0.9, 'p/l=%s' % text)
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
call,put,put_mult = 11, 0, 1.

short_call_result = test_strategy(short_call, call)
long_put_result = test_strategy(long_put, put)
res = pd.DataFrame(short_call_result)
res['put_strike'] = long_put_result['put_strike']
res['put_premium'] = long_put_result['put_premium']
res['put p/l'] = long_put_result['put p/l']
res['stock p/l'] = put_mult*100.*(res['expiry_price'] - res['underlying_price'])

res['aux'] = 100*(res['expiry_price'] - res.loc[0,'underlying_price'])
totl, i = 0,0
for index, r in res.iterrows():
    pl = r['stock p/l'] + r['call p/l'] + r['put p/l']
    totl += pl
    res.loc[i,'total'] = totl
    i += 1
name = '%d-%d-%.1f' % (call,put,put_mult)

plot(res,'text',name)
res.to_csv('../out/trad-%s.csv' % name)

