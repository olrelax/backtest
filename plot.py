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
    df['date'] = pd.to_datetime(df['date'])
    df = df.loc[(df['action'] != 'o1') | (df['action'] != 'o2')]
    if gv.param_2 is not None:
        df = df.loc[(df['action'] == 'c2') | (df['action'] == 'v2')]

    if gv.ini('plot_all'):
        numeric_cols = ['stock', 'real_sum_1', 'real_sum_2', 'unreal_sum_1', 'unreal_sum_2', 'portfolio', 'profit_sum']
    elif not gv.ini('plot_non_trade_days'):
        df = df.loc[(df['action'] != 'v1') & (df['action'] != 'v2')]
        numeric_cols = ['stock', 'real_sum_1', 'real_sum_2', 'profit_sum']
    else:
        numeric_cols = ['stock','unreal_sum_1','unreal_sum_2','portfolio']

    df_date = df[['date']]
    show_stock = gv.ini('show_stock')
    df_numeric = df[numeric_cols]  # .drop(columns='action')
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

