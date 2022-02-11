import pandas as pd
def merge():
    df = pd.DataFrame({'d': ['m24','m24','m1','m1','t2','t2','m8','m8','t9','t9'],
                       'e': ['m1','m1','t9','t9','t9','t9','m15','m15','m15','m15'],
                       's':[100,101,111,112,111,112,131,132,131,132]})
    df_exp = df[['e']].drop_duplicates(subset='e')
    print(df_exp)
    df = df_exp.merge(df,left_on='e',right_on='d')
    print(df)

def dic():
    d = {'type': ['C','C','C'], 'side': ['S', 'S', 'L']}
    print(type(d))
    a = [1,2]
    print(type(a))
    b = (1,2)
    print(type(b))

def learn():
    merge()
if __name__ == '__main__':
    dic()
