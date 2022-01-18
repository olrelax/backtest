import pandas as pd
from datetime import datetime
from au import prn, s2d, d2s, add_days,read_stock,get_monthly_opts
from os import system
from neural_net import get_nn,train,save_nn_input
import globalvars as gv
from position import Position,getz,delz,listz
from transactions import close_positions, open_position
from plot import plot
from shutil import copyfile
def archive():
    arc_filename = 'options-' + datetime.now().strftime('%Y-%m-%d--%H-%M')
    cmd = 'tar cvf ../Archive/%s.tar *.py config.ini  2>/dev/null' % arc_filename
    system(cmd)


epoc_start = datetime.strptime('0010-01-01', '%Y-%m-%d')
def reset_test():
    gv.last_read_fn = ''
    gv.current_month = 0
    gv.opts_full, gv.opts_full_next_year = None, None

SHORT,LONG = -1, 1
def make_res_df():
    df = pd.DataFrame({'date': [epoc_start], 'stock': [0.0],
                       'open_date':[epoc_start],'expiration': [epoc_start],'strike': [0.0],'premium': [0.0],'last_price':[0.0],'margin_s': [0.0],'margin_l': [0.0],
                       'profit_s':[0.0],'profit_l':[0.0],
                       'profit_sum':[0.0],'details': [''],'right_strike':[0.0],'action':['']})

    return df
def copy_z(z: Position,row: pd.Series):
    if z.is_short():
        row['margin_s'] = z.pos_margin()
        row['margin_l'] = 0
    elif z.is_long():
        row['margin_l'] = z.pos_margin()
        row['margin_s'] = 0
    else:
        row['margin_s'] = 0
        row['margin_l'] = 0

    row['profit_s'] = gv.profit_s
    row['profit_l'] = gv.profit_l
    row['profit_sum'] = gv.profit_sum
    row['details'] = z.comment
    row['open_date'] = d2s(z.open_date())
    row['expiration'] = d2s(z.expiration)
    row['premium'] = z.enter_price
    row['last_price'] = z.last_price
    row['strike'] = z.strike
    row['stock'] = z.underlying
    row['right_strike'] = z.right_strike
    act = 'o' if z.is_open() else 'c' if z.is_closed() else 'err'
    sl = 's' if z.is_short() else 'l' if z.is_long() else '???'
    row['action'] = act + sl
    if gv.get_atm:
        row['atm'] = z.atm

def del_items(za,del_list):
    z_len = len(za)
    new_za = []
    for i in range(z_len):
        if i not in del_list:
            new_za.append(za[i])
    return new_za
#   ********************************  TRADE  *******************************************
def backtest():
    print('run trade...')
    if gv.stock is None:
        gv.stock = read_stock()
    if gv.ed is None:
        gv.ed = d2s(gv.stock['date'].iloc[-1])
    res = make_res_df()
    reset_test()
    zsa = []
    zla = []
    gv.profit_s,gv.profit_l,gv.profit_sum = 0.,0.,0.
    first_trade_day = s2d(gv.bd)
    last_trade_day = s2d(gv.ed)
    opts = None
    gv.exclude_bound = gv.exclude_period.split(' ') if gv.exclude_period else None
    row = pd.Series(res.copy().iloc[0])
    profit_trades, loss_trades, trades, max_loss = 0, 0, 0, 0.0
    for idx, q in gv.stock.iterrows():
        date = q['date']
        q_open = q['open']
        if date < first_trade_day:
            continue
        if date > last_trade_day:
            break
        volatility = q['volatility']
        row['date'] = d2s(date)
        if date == s2d('2019-12-13'):
            print()
        print(date)
        opts = get_monthly_opts(date,opts,gv.short_type)
        target_exp = add_days(date, gv.days2exp)
        # --------------------------------- CLOSE ----------------------------
        zsa_len = len(zsa)
        del_list_s = []
        del_list_l = []
        for i in range(zsa_len):
            day_pl = 0
            zs = zsa[i]
            close_positions(opts, date, zs, volatility, q_open)
            if zs.close_date() == date and zs.is_closed():
                gv.profit_sum += zs.pos_profit()
                gv.profit_s += zs.pos_profit()
                copy_z(zs, row)
                res = res.append(row,ignore_index=True)
                del_list_s.append(i)
                day_pl = zs.pos_profit()
                if day_pl > 0:
                    profit_trades += 1
                elif day_pl < 0:
                    loss_trades += -1
                trades += 1
                if gv.long_param:
                    zl = zla[i]
                    close_positions(opts, date, zl, 0, q_open,zs)
                    gv.profit_sum += zl.pos_profit()
                    gv.profit_l += zl.pos_profit()
                    day_pl += zl.pos_profit()
                    copy_z(zl,row)
                    res = res.append(row,ignore_index=True)
                    del_list_l.append(i)

            max_loss = min(max_loss, day_pl)
        zsa = del_items(zsa,del_list_s)
        if gv.long_param:
            zla = del_items(zla,del_list_l)
        # --------------------------------- OPEN ----------------------------
        if date == last_trade_day:
            break

        zs = Position(gv.short_type, SHORT)
        open_position(opts, date, target_exp, zsa, zs, volatility)
        if zs.is_open():
            zsa.append(zs)
            copy_z(zs,row)
            res = res.append(row, ignore_index=True)

            if gv.long_param:
                zl = Position(gv.long_type, LONG)
                if gv.algo_long == 'hedge_distance':
                    long_param = zs.strike - gv.long_param
                else:
                    long_param = None
                open_position(opts, date, target_exp, zla, zl, volatility,long_param)
                if zl.is_open():
                    zla.append(zl)
                    copy_z(zl,row)
                    res = res.append(row, ignore_index=True)

        if gv.long_param and not len(zsa) == len(zla):
            exit('asymmetry detected')

        listz(zsa,'eod state:')
        if gv.long_param:
            listz(zla,'eod state:')


# -------------------------------- END ITERATION -----------------------------------------
    prn('End', 'yellow')
    d_now = datetime.now()
    sd_now = datetime.strftime(d_now, '%dd%Hh%Mm%Ss')
    gv.suffix = ' sp %.2f, lp %.2f' % (gv.short_param, gv.long_param if gv.long_param is not None else 0)
    fn_base = '%s %s' % (sd_now,gv.suffix)
    res = res.reset_index(drop=True)
    res = res.drop(axis=0, index=0)
    res.to_csv('../out/e-%s.csv' % fn_base, index=False)
    copyfile('config.ini','../out/i-%s.ini' % fn_base)
    save_nn_input(res, gv.vlt_sample_size)
    archive()
    txt = 'profits=%d, losses=%d, trades=%d, max loss=%.2f' % (profit_trades,loss_trades,trades,max_loss)
    plot(fn_base,txt)

#################################### END BACKTEST ########################################################
def iterate_bt(test=False):
    gv.show = False
    sp_start = gv.short_param
    lp_start = gv.long_param
    sp_range = gv.ini('sp_range')
    lp_range = gv.ini('lp_range')
    sp_expr = gv.ini('sp_expr')
    lp_expr = gv.ini('lp_expr')
    for p in range(5):

        gv.trade_day_of_week = p +1
        for sp in range(sp_range):
            gv.short_param = eval(sp_expr)
            for lp in range(lp_range):
                gv.long_param = eval(lp_expr)
                print('p=%d sp %.2f, lp %.3f' % (gv.trade_day_of_week,gv.short_param, gv.long_param))
                if not test:
                    backtest()
    system('say the task is done')

############################################################################################
def run(task=''):
    gv.read_ini()
    gv.sample_len = get_nn([]) if gv.algo_short == 'nn' else gv.vlt_sample_size

    if task == '':
        backtest()
    elif task == 'nn':
        train()
    elif task == 'p':
        plot('xls')
    elif task == 'a':
        archive()
    elif task == 'i':
        iterate_bt(test=False)
    elif task == 'i_test':
        iterate_bt(test=True)


if __name__ == '__main__':
    a = gv.ini('task','')
    run(a)
