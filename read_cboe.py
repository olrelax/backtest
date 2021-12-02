import pandas as pd
from os import walk
d = '../SPY_2020/'
i = 0
f = []
for (path, names, filenames) in walk(d):
    f.extend(filenames)
    break
f.sort()

rf = None
for fn in f:
    raw = pd.read_csv('%s/%s' % (d,fn))
    cf = raw.loc[raw['option_type'] == 'P'].loc[raw['underlying_bid_1545'] - 15 < raw['strike']].loc[
        raw['strike'] < raw['underlying_bid_1545'] + 15]
    if i == 0:
        rf = cf.copy()
    else:
        rf = rf.append(cf.copy())
    i += 1
    if i > 10:
        break
rf.reset_index(drop=True).to_csv('../out/f.csv')

