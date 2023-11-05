import pandas as pd
import inspect

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    if name.find('/') > 0:
        df_path = name
    else:
        df_path = '../devel/%s.csv' % name
    dtf.to_csv(df_path,index=False)
    print('save %s done' % name)
    if stop:
        exit()

opt = pd.read_csv('../devel/otm-7.csv')
vix = pd.read_csv('../data/other/VIX.csv')
opt['quote_date'] = pd.to_datetime(opt['quote_date'])
vix['Date'] = pd.to_datetime(vix['Date'])
df = pd.merge(opt,vix,left_on='quote_date',right_on='Date')
save(df)