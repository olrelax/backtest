import pandas as pd
from os import walk
from au import s2d
d = '../data/SPY_2020_CBOE_FILES/'
i = 0
f = []
for (path, names, filenames) in walk(d):
    f.extend(filenames)
    break
f.sort()

rf = None
for fn in f:
    raw = pd.read_csv('%s/%s' % (d,fn))
    qd = raw['quote_date'].iloc[0]
    if qd == '2020-03-11':
        dev = 61
    elif qd == '2020-06-15':
        dev = 25
    elif qd == '2020-08-17':
        dev = 20
    else:
        dev = 15
    cf = raw.loc[raw['option_type'] == 'P'].loc[raw['underlying_bid_1545'] - dev < raw['strike']].loc[
        raw['strike'] < raw['underlying_bid_1545'] + dev]
    if i == 0:
        rf = cf.copy()
    else:
        rf = rf.append(cf.copy())
    i += 1
rf.reset_index(drop=True).to_csv('../data/SPY_CBOE_2020_PUT.csv')

