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

def plot(df,txt,lines_count,draw_or_show,fn):

    if lines_count == 1:
        dfp = df[['exit_date', 'sum_0']]
    else:
        cols = 'exit_date,'
        for i in range(lines_count):
            cols = cols + 'sum_%d,' % i
        cols = cols + 'sum'
        dfp = df[cols.split(',')]
    dfp = dfp.set_index('exit_date')
    ax = dfp.plot(figsize=(11, 7), title=txt)
    xtick = pd.date_range(start=dfp.index.min(), end=dfp.index.max(), freq='M')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    #ax.set_ylim(ylim_bottom, ylim_top)
    plt.savefig('../out/c-%s.png' % fn)

    if draw_or_show == 'draw':
        plt.draw()
    else:
        plt.show()
    plt.pause(0.0001)
    if draw_or_show == 'draw':
        plt.close()
