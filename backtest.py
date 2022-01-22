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
from learning import learn
from prepare_data import process_data
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
def make_res_df_0():
    df = pd.DataFrame({'date': [epoc_start], 'stock': [0.0],
                       'open_date':[epoc_start],'expiration': [epoc_start],'strike': [0.0],'premium': [0.0],'last_price':[0.0],'margin_s': [0.0],'margin_l': [0.0],
                       'profit_s':[0.0],'profit_l':[0.0],
                       'profit_sum':[0.0],'details': [''],'right_strike':[0.0],'action':['']})

    return df
def make_res_df():
    df = pd.DataFrame({'date': [epoc_start], 'stock': [0.0]})
    return df

def copy_z(z: Position,row: pd.Series):

    row['open_date'] = d2s(z.get_open_date())
    row['expiration'] = d2s(z.get_expiration())
    row['strike'] = z.get_strike()
    row['premium'] = z.get_enter_price()
    row['last_price'] = z.get_last_price()
    # if z.is_primary:
    #    row['margin_1'] = z.pos_margin()
    #    row['margin_2'] = 0
    # else:
    #    row['margin_1'] = 0
    row['margin'] = z.pos_margin()
    row['pl_1'] = gv.pl_1
    row['pl_2'] = gv.pl_2
    row['profit_sum'] = gv.profit_sum
    row['details'] = z.comment
    row['stock'] = z.underlying
    row['right_strike'] = z.right_strike
    act = 'o' if z.is_open() else 'c' if z.is_closed() else 'err'
    sl = '1' if z.is_primary else '2'
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
def get_latest_trade_day(date):
    if date is None:
        return gv.stock['date'].iloc[-1]
    else:
        return gv.stock.loc[gv.stock['date'] <= s2d(date)]['date'].iloc[-1]
def backtest():
    if gv.stock is None:
        gv.stock = read_stock()
    res = make_res_df()
    reset_test()
    basket_1 = []
    basket_2 = []
    gv.pl_1,gv.pl_2,gv.profit_sum = 0.,0.,0.
    first_trade_day = s2d(gv.bd)
    last_trade_day = get_latest_trade_day(gv.ed)
    gv.ed = d2s(last_trade_day)
    opts_1,opts_2 = None,None
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
        if date == s2d('2021-02-01'):
            print('bp')
        print(date)
        opts_1 = get_monthly_opts(date,opts_1,gv.option_type_1)
        if gv.option_type_2 == gv.option_type_1:
            opts_2 = opts_1
        else:
            opts_2 = get_monthly_opts(date,opts_2,gv.option_type_2)
        target_exp_1 = add_days(date, gv.days2exp_1)
        target_exp_2 = add_days(date, gv.days2exp_2)
        # --------------------------------- CLOSE ----------------------------
        basket_1_len = len(basket_1)
        basket_2_len = len(basket_2)
        del_list_1 = []
        del_list_2 = []
        day_pl_1, day_pl_2 = 0,0
        if gv.param_1:
            for i in range(basket_1_len):
                z1 = basket_1[i]
                close_positions(opts_1, date, z1, volatility, q_open)
                if z1.get_close_date() == date and z1.is_closed():
                    gv.profit_sum += z1.pos_profit()
                    gv.pl_1 += z1.pos_profit()
                    copy_z(z1, row)
                    res = res.append(row,ignore_index=True)
                    del_list_1.append(i)
                    trade_pl_1 = z1.pos_profit()
                    day_pl_1 += trade_pl_1
                    trades += 1

        if gv.param_2:
            for i in range(basket_2_len):
                z2 = basket_2[i]
                close_positions(opts_2, date, z2, 0, q_open)
                if z2.get_close_date() == date and z2.is_closed():
                    gv.profit_sum += z2.pos_profit()
                    gv.pl_2 += z2.pos_profit()
                    trade_pl_2 = z2.pos_profit()
                    day_pl_2 += trade_pl_2
                    copy_z(z2,row)
                    res = res.append(row,ignore_index=True)
                    del_list_2.append(i)

        max_loss = min(max_loss, day_pl_1 + day_pl_2)
        basket_1 = del_items(basket_1,del_list_1)
        if gv.param_2:
            basket_2 = del_items(basket_2,del_list_2)
        # --------------------------------- OPEN ----------------------------
        if date == last_trade_day:
            break

        parent_position = None
        z1 = Position(gv.option_type_1, gv.side_1,primary=True,call_pair_close=True)
        if gv.param_1:
            open_position(opts_1, date, gv.algo_1, target_exp_1, basket_1, z1, volatility,gv.param_1)
            if z1.is_open():
                basket_1.append(z1)
                copy_z(z1,row)
                res = res.append(row, ignore_index=True)
                parent_position = z1

        if gv.param_2:
            z2 = Position(gv.option_type_2, gv.side_2)
            if gv.algo_2[:5] == 'hedge':
                if z1.is_open():
                    if gv.algo_2 == 'hedge_distance':
                        param_2 = parent_position.get_strike() - gv.param_2
                    elif gv.algo_2 == 'hedge_discount':
                        param_2 = parent_position.get_enter_price() * gv.param_2
                    else:
                        param_2 = None
                else:
                    param_2 = None
            else:
                param_2 = gv.param_2
            open_position(opts_2, date, gv.algo_2, target_exp_2, basket_2, z2, volatility,param_2)
            if z2.is_open():
                basket_2.append(z2)
                copy_z(z2,row)
                res = res.append(row, ignore_index=True)


        listz(basket_1,'eod state:')
        if gv.param_2:
            listz(basket_2,'eod state:')


# -------------------------------- END ITERATION -----------------------------------------
    prn('End', 'yellow')
    d_now = datetime.now()
    sd_now = datetime.strftime(d_now, '%dd%Hh%Mm%Ss')
    gv.suffix = ' sp %.2f, lp %.2f' % (gv.param_1, gv.param_2 if gv.param_2 is not None else 0)
    fn_base = '%s %s' % (sd_now,gv.suffix)
    res = res.reset_index(drop=True)
    res = res.drop(axis=0, index=0)
    res = res[['date','stock','open_date','expiration','strike','premium','last_price','margin','pl_1','pl_2','profit_sum','details','action']]

    res.to_csv('../out/e-%s.csv' % fn_base, index=False)
    copyfile('config.ini','../out/i-%s.ini' % fn_base)
    archive()
    txt = 'profits=%d, losses=%d, trades=%d, max loss=%.2f' % (profit_trades,loss_trades,trades,max_loss)
    plot(fn_base,txt)

#################################### END BACKTEST ########################################################
def iterate_bt(test=False):
    gv.show = False
    sp_start = gv.param_1
    lp_start = gv.param_2
    sp_range = gv.ini('sp_range')
    lp_range = gv.ini('lp_range')
    sp_expr = gv.ini('sp_expr')
    lp_expr = gv.ini('lp_expr')
    for p in range(5):

        gv.trade_day_of_week = p +1
        for sp in range(sp_range):
            gv.param_1 = eval(sp_expr)
            for lp in range(lp_range):
                gv.param_2 = eval(lp_expr)
                print('p=%d sp %.2f, lp %.3f' % (gv.trade_day_of_week,gv.param_1, gv.param_2))
                if not test:
                    backtest()
    system('say the task is done')

############################################################################################
def run(task=''):
    gv.read_ini()

    if task == '':
        backtest()
    elif task == 'nn':
        train()
    elif task == 'p':
        plot('last')
    elif task == 'a':
        archive()
    elif task == 'i':
        iterate_bt(test=False)
    elif task == 'i_test':
        iterate_bt(test=True)
    elif task == 'learn':
        learn()
    elif task[:4] == 'data':
        task_set = task.split(',')
        if len(task_set) == 2:
            process_data(task_set[1])
        elif len(task_set) == 4:
            process_data(task_set[1],task_set[2],task_set[3])
        elif task == 'data':
            process_data('d')
            process_data('r','2022','P')
            process_data('r','2022','C')
            process_data('h')

if __name__ == '__main__':
    a = gv.ini('task','')
    run(a)
