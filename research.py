import pandas as pd
'''
0   underlying_symbol    1070 non-null   object 
 1   quote_date           1070 non-null   object 
 2   root                 1070 non-null   object 
 3   expiration           1070 non-null   object 
 4   strike               1070 non-null   float64
 5   option_type          1070 non-null   object 
 6   open                 1070 non-null   float64
 7   high                 1070 non-null   float64
 8   low                  1070 non-null   float64
 9   close                1070 non-null   float64
 10  trade_volume         1070 non-null   int64  
 11  bid_size_1545        1070 non-null   int64  
 12  bid_1545             1070 non-null   float64
 13  ask_size_1545        1070 non-null   int64  
 14  ask_1545             1070 non-null   float64
 15  underlying_bid_1545  1070 non-null   float64
 16  underlying_ask_1545  1070 non-null   float64
 17  bid_size_eod         1070 non-null   int64  
 18  bid_eod              1070 non-null   float64
 19  ask_size_eod         1070 non-null   int64  
 20  ask_eod              1070 non-null   float64
 21  underlying_bid_eod   1070 non-null   float64
 22  underlying_ask_eod   1070 non-null   float64
 23  vwap                 1070 non-null   float64
 24  open_interest        1070 non-null   int64  
 25  delivery_code        0 non-null      float64
'''

def p(df,h=10):
    print(df.head(h))
fn = '../../Algonavt/data/init/quotes/SPY.csv'
spy = pd.read_csv(fn,delimiter='\t').rename(columns={'2009.12.31': 'date','111.44': 'close','0.0':'f1','90637900.0':'f2','0.0.1':'f3'})

spy = spy.loc[spy['date'] > '2020.01.01'].copy().reset_index(drop=True)

for i, r in spy.iterrows():
    if i > 3:
        s = spy.loc[i, 'close']
        b = spy.loc[i - 4, 'close']
        p = (s - b)/b
        spy.loc[i,'f1'] = s - b
        spy.loc[i, 'f2'] = p*100
        spy.loc[i, 'f3'] = b

    else:
        spy.loc[i, 'f2'] = 0
for dd in range(2,12,):
    sh = spy.loc[spy['f2'] < -dd].shape[0]
    print(dd,sh)
sh = spy.loc[spy['f2'] < -4]

print(sh.head(sh.shape[0]))
sh.to_csv('../sh.csv')
