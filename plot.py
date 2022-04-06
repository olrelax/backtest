import pandas as pd
import matplotlib.pyplot as plt
ylim_bottom = -100
ylim_top = 100

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
