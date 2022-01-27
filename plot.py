import pandas as pd
import matplotlib.pyplot as plt
import globalvars as gv
def plot(src,txt=''):
    show = gv.show
    if src == 'last':
        last_file = open('../out/last_file','r')
        fn = last_file.read().rstrip('\n')
        path = '../out/e-%s.csv' % fn
        save = False
        show = True
    elif src == 'plot_csv':
        save = False
        show = True
        path = '../out/%s.csv' % gv.ini('plot_csv')
    else:
        path = '../out/e-%s.csv' % src
        save = True
    df = pd.read_csv(path)
    # df = df.loc[(df['action'] == 'c2') | (df['action'] == 'v2')]  # right day p/l appears after option_2 close
    df = df.loc[(df['action'] == 'c2') | (df['action'] == 'c1')]  # right day p/l appears after option_2 close
    df['date'] = pd.to_datetime(df['date'])
    df_date = df[['date']]
    show_stock = gv.ini('show_stock')
    numeric_cols = ['stock','unreal_sum_1','unreal_sum_2','portfolio','profit_sum','action']
    df_numeric = df[numeric_cols].drop(columns='action')
    if show_stock:
        df_numeric = (df_numeric - df_numeric.mean()) / df_numeric.std()
        # df = (df - df.min()) / (df.max() - df.min())
    else:
        df_numeric = df_numeric.drop(columns='stock')

    df = df_date.join(df_numeric)
    df = df.set_index('date')
    df.to_csv('../out/last_plot.csv')
    ax = df.plot(figsize=(14, 8), subplots=False,title=txt)
    xtick = pd.date_range(start=df.index.min(), end=df.index.max(), freq='W')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    ylim_bottom = gv.ini('ylim_bottom')
    ylim_top = gv.ini('ylim_top')
    if ylim_top is not None and ylim_top is not None:
        ax.set_ylim(ylim_bottom,ylim_top)
    if not src == 'last':
        last_file = open('../out/last_file','w')
        print('%s' % src,file=last_file)
        last_file.close()
    if save:
        full_fn_path = '../out/c-%s.png' % src
        plt.savefig(full_fn_path)
    if show:
        plt.show()

