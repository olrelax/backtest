import pandas as pd
from au import s2d
df = pd.DataFrame({'date':['11/8/2011'],'stock':[428.0]})

df['date'] = pd.to_datetime(df['date'])
row = pd.Series(df.loc[0])
row['stock'] = 54
df.iloc[0] = row
row['stock'] = 33
row['date'] = s2d('2021-01-12')
df = df.append(row,ignore_index=True)

print(df)
#res = pd.concat([res,df],ignore_index=True)
#print(res)

exit()
#df = pd.DataFrame(columns=('a','b'))
df1 = df.copy()
lst = ['va','vb']
ser = pd.Series(lst)
df.loc[0] = lst
row = df.iloc[0]
df.loc[0]['a'] = 'a1'
row['b'] = 'b1'
df1 = pd.concat([df1,df],ignore_index=True)
df.loc[0]['a'] = 'a2'
row['b'] = 'b2'
df1 = pd.concat([df1,df],ignore_index=True)
print(df1)

