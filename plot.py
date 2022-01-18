import pandas as pd
import matplotlib.pyplot as plt
import globalvars as gv
def plot(src,txt=''):
    show = gv.show
    if src == 'xls':
        save = False
        show = True
        path = '../out/%s.csv' % gv.ini('xls')
    else:
        path = '../out/e-%s.csv' % src
        save = True
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    act_sl = 'cl' if gv.long_param else 'cs'
    hide_open = gv.ini('hide_open')
    if gv.get_atm:
        if gv.long_param is not None:
            df = df[['profit_s','profit_l','profit_sum','action']]
        else:
            df = df[['profit_s','action']]
    else:
        if gv.long_param is not None:
            df = df[['profit_s','profit_l','profit_sum','action']]
        else:
            df = df[['profit_s','action']]
    if hide_open:
        df = df.loc[df['action'] == act_sl]
    df.drop(columns='action')

    # df = (df - df.mean()) / df.std()
    # df = (df - df.min()) / (df.max() - df.min())

    ax = df.plot(figsize=(14, 8), subplots=False,title=txt)


    xtick = pd.date_range(start=df.index.min(), end=df.index.max(), freq='W')
    ax.set_xticks(xtick, minor=True)
    ax.grid('on', which='minor')
    ax.grid('on', which='major')
    ylim_bottom = gv.ini('ylim_bottom')
    ylim_top = gv.ini('ylim_top')
    if ylim_top is not None and ylim_top is not None:
        ax.set_ylim(ylim_bottom,ylim_top)
    if save:
        full_fn_path = '../out/c-%s.png' % src
        plt.savefig(full_fn_path)
    if show:
        plt.show()

