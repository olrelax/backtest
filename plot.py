import pandas as pd
import matplotlib.pyplot as plt
import inspect

ylim_bottom = -100
ylim_top = 100
def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
    if stop:
        exit()




def custom_plot(df,x,y):
    df = df.reset_index(drop=True)
    # dfp.plot(x='quote_datetime',figsize=(11, 7),subplots=True)
    df.plot(x=x,y=y,subplots=True)
    plt.show()
    plt.pause(0.0001)
def custom_plot_(df,a,b):
    # dfp.plot(x='quote_datetime',figsize=(11, 7),subplots=True)
    # dfp.plot(y=['bid','underlying_ask'],subplots=True)
    plt.plot(df['quote_datetime'],df['bid'])
    plt.show()
    plt.pause(0.0001)

def plot(df,x_axis,txt,fn,opt_count,stock,plot_raw):
    cols = '%s,' % x_axis
    if opt_count > 1:
        for i in range(opt_count):
            cols = cols + 'opt_sum_%d,' % i
        cols = cols + 'opt_sum'
    else:
        cols = cols + 'opt_sum'
    if plot_raw == 'y':
        cols = cols + ',raw_sum'
    if stock in ('plot','ltrade','strade'):
        cols = cols + ',stock'
    if 'under_sum' in df.columns and stock in ('ltrade','strade'):
        cols = cols + ',under_sum'
        cols = cols + ',sum'
    dfp = df[cols.split(',')]
    dfp = dfp.set_index(x_axis)
    # save(dfp,'df_plot')
    ax = dfp.plot(figsize=(11, 7), title=txt)
    if len(dfp) > 32:
        freq = 'M'
        xtick = pd.date_range(start=dfp.index.min(), end=dfp.index.max(), freq=freq)
        ax.set_xticks(xtick, minor=False)   # play with parameter
        ax.grid('on', which='minor')
        ax.grid('on', which='major')
    plt.savefig('../out/%s-p.png' % fn)
    plt.show()
