import pandas as pd
from datetime import datetime
from au import prn, s2d, d2s, add_work_days,read_stock,get_monthly_opts,get_latest_trade_day
from os import system
import globalvars as gv
from position import Position,listz
from transactions import close_routine, open_routine,option_value
from plot import plot
from shutil import copyfile
from learning import learn
from prepare_data import process_data
def archive():
    arc_filename = 'options-' + datetime.now().strftime('%Y-%m-%d--%H-%M')
    cmd = 'tar cvf ../Archive/%s.tar *.py config.ini  2>/dev/null' % arc_filename
    system(cmd)


gv.epoc_start = datetime.strptime('0010-01-01', '%Y-%m-%d')

SHORT,LONG = -1, 1

def copy_z(date,z: Position):
    rec = pd.Series({'date': [gv.epoc_start], 'stock': [0.0]})
    rec['date'] = date
    rec['open_date'] = d2s(z.open_date())
    rec['expiration'] = d2s(z.expiration())
    rec['strike'] = z.strike()
    rec['premium'] = z.enter_price()
    rec['current'] = z.current()
    rec['real_sum_1'] = gv.real_sum_1
    rec['real_sum_2'] = gv.real_sum_2
    rec['unreal_sum_1'] = gv.real_sum_and_curr_pl_1
    rec['unreal_sum_2'] = gv.real_sum_and_curr_pl_2
    rec['profit_sum'] = gv.profit_sum
    rec['portfolio'] = gv.portfolio
    rec['details'] = z.comment
    rec['stock'] = z.underlying
    rec['right_strike'] = z.right_strike
    act = 'o' if z.is_open() and date == z.open_date() else 'v' if  z.is_open() else 'c' if z.is_closed() else 'err'
    sl = '1' if z.is_primary else '2'
    rec['action'] = act + sl
    if gv.get_atm:
        rec['atm'] = z.atm
    return rec


#   ********************************  TRADE  *******************************************
def backtest():
    if gv.stock is None:
        gv.stock = read_stock()
    res = pd.DataFrame([])
    gv.reset_test()
    gv.pl_1,gv.pl_2,gv.profit_sum = 0.,0.,0.
    first_trade_day = s2d(gv.bd)
    last_trade_day = get_latest_trade_day(gv.ed)
    gv.ed = d2s(last_trade_day)
    opts_1,opts_2 = None,None
    gv.exclude_bound = gv.exclude_period.split(' ') if gv.exclude_period else None
    profit_trades, loss_trades, trades, max_loss = 0, 0, 0, 0.0
    z1 = Position(gv.option_type_1, gv.side_1)
    z2 = Position(gv.option_type_2, gv.side_2)
    for idx, q in gv.stock.iterrows():
        date = q['date']
        open_instruction_1,open_instruction_2 = '',''
        q_open = q['open']
        if date < first_trade_day:
            continue
        if date > last_trade_day:
            break
        y = date.year
        m = date.month
        d = date.day
        if y == 2020:
            if m == 1:
                if d == 21:
                    print()
        print(date)
        volatility = q['volatility']
        opts_1 = get_monthly_opts(date,opts_1,gv.option_type_1)
        if gv.option_type_2 == gv.option_type_1:
            opts_2 = opts_1
        else:
            opts_2 = get_monthly_opts(date,opts_2,gv.option_type_2)
        target_exp_1 = add_work_days(date, gv.days2exp_1)
        target_exp_2 = add_work_days(date, gv.days2exp_2)
        # --------------------------------- CLOSE ----------------------------
        day_pl_1, day_pl_2 = 0,0
        if gv.param_1 and z1.open_date() > gv.epoc_start:
            close_routine(opts_1, date, z1, volatility, q_open)
            if z1.close_date() == date:
                trade_pl_1 = z1.margin() - z1.close_commission
                gv.profit_sum += trade_pl_1
                gv.real_sum_1 += trade_pl_1
                gv.cash += z1.current() * z1.side() - z1.close_commission
                gv.portfolio = gv.cash + z2.value()
                trades += 1
                open_instruction_1 = 'force_open'
            else:
                gv.real_sum_and_curr_pl_1 = gv.real_sum_1 + z1.value()
                gv.portfolio = gv.cash + z1.value() + z2.value()
            res = res.append(copy_z(date,z1), ignore_index=True)

        if gv.param_2 and z2.open_date() > gv.epoc_start:
            close_routine(opts_2, date, z2, 0, q_open)
            if z2.close_date() == date:
                trade_pl_2 = z2.margin() - z2.close_commission
                gv.profit_sum += trade_pl_2
                gv.real_sum_2 += trade_pl_2
                gv.cash += z2.current() * z2.side() - z2.close_commission
                gv.portfolio = gv.cash + z1.value()
                trades += 1
                open_instruction_2 = 'force_open'
            else:
                gv.real_sum_and_curr_pl_2 = gv.real_sum_2 + z2.value()
                gv.portfolio = gv.cash + z1.value() + z2.value()
            res = res.append(copy_z(date,z2), ignore_index=True)

        max_loss = min(max_loss, day_pl_1 + day_pl_2)
        # --------------------------------- OPEN ----------------------------
        if date == last_trade_day:
            break
        if gv.param_1 and z1.is_closed():
            z = open_routine(gv.option_type_1, gv.side_1, True, opts_1,date, gv.algo_1, target_exp_1, volatility,gv.param_1,open_instruction=open_instruction_1)
            if z is not None and z.open_date() == date:
                z1 = z
                gv.cash -= z1.enter_price() * z1.side() + gv.comm
                gv.portfolio = gv.cash + z1.value() + z2.value()
                res = res.append(copy_z(date,z), ignore_index=True)

        if gv.param_2 and z2.is_closed():
            if gv.algo_2[:5] == 'hedge':
                if z1 is not None:
                    if gv.algo_2 == 'hedge_distance':
                        param_2 = z1.strike() - gv.param_2
                    elif gv.algo_2 == 'hedge_discount':
                        param_2 = z1.enter_price() * gv.param_2
                    else:
                        param_2 = None
                else:
                    param_2 = None
            else:
                param_2 = gv.param_2
            z = open_routine(gv.option_type_2, gv.side_2,False,opts_2,  date, gv.algo_2, target_exp_2,  volatility,param_2,open_instruction=open_instruction_2)
            if z is not None and z.open_date() == date:
                z2 = z
                gv.cash -= z2.enter_price() * z2.side() + gv.comm
                gv.portfolio = gv.cash + z1.value() + z2.value()
                res = res.append(copy_z(date,z), ignore_index=True)



# -------------------------------- END ITERATION -----------------------------------------
    prn('End', 'yellow')
    d_now = datetime.now()
    sd_now = datetime.strftime(d_now, '%dd%Hh%Mm%Ss')
    gv.suffix = ' sp %.2f, lp %.2f' % (gv.param_1, gv.param_2 if gv.param_2 is not None else 0)
    fn_base = '%s %s' % (sd_now,gv.suffix)

    res = res.reset_index(drop=True)
    res = res.loc[(res['action'] == 'o1') | (res['action'] == 'o2') | (res['action'] == 'c1') | (res['action'] == 'c2')]
    # res['portfolio'] = res['portfolio'] - res['portfolio'].iloc[0]
    # res = res[['date','stock','open_date','expiration','strike','premium','last_price','margin_1','margin_2','pl_1','pl_2','profit_sum','cash','details','action']]

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
    trade_day_of_week = 1
    for p in range(5):

        gv.trade_day_of_week = p + 1
        for sp in range(sp_range):
            gv.param_1 = eval(sp_expr)
            for lp in range(lp_range):
                gv.param_2 = eval(lp_expr)
                print('p=%d sp %.2f, lp %.3f' % (trade_day_of_week,gv.param_1, gv.param_2))
                if not test:
                    backtest()
    system('say the task is done')

############################################################################################
def run(task=''):
    gv.read_ini()

    if task == '':
        backtest()
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
