import pandas as pd
from datetime import datetime
from au import prn, s2d, d2s, add_work_days,read_stock,get_monthly_opts,get_latest_trade_day
from os import system
import globalvars as gv
from position import Position,listz
from transactions import close_routine, open_routine
from plot import plot
from shutil import copyfile
from learning import learn
from prepare_data import process_data

def copy_z(z: Position,row: pd.Series):

    row['open_date'] = d2s(z.get_open_date())
    row['expiration'] = d2s(z.get_expiration())
    row['strike'] = z.get_strike()
    row['premium'] = z.get_enter_price()
    row['last_price'] = z.get_last_price()
    if z.is_primary:
        row['margin_1'] = z.pos_margin()
        row['margin_2'] = 0
    else:
        row['margin_1'] = 0
        row['margin_2'] = z.pos_margin()
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

def backtest():
    if gv.stock is None:
        gv.stock = read_stock()
    res = pd.DataFrame({'date': [epoc_start], 'stock': [0.0]})

    gv.reset_test()
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
    if gv.trade_day_of_week_1 is None and gv.trade_day_of_week_2 is None:
        max_position_count = None
    elif isinstance(gv.trade_day_of_week_1,int):
        max_position_count = 1
    elif isinstance(gv.trade_day_of_week_1,str):
        max_position_count = 1  # len(days_list)
    else:
        max_position_count = -1
    for idx, q in gv.stock.iterrows():
        date = q['date']
        force_open_1,force_open_2 = False, False
        if date == s2d('2020-04-09'):
            print('>{}'.format(date))
        q_open = q['open']
        if date < first_trade_day:
            continue
        if date > last_trade_day:
            break
        print(date)
        volatility = q['volatility']
        row['date'] = d2s(date)
        opts_1 = get_monthly_opts(date,opts_1,gv.option_type_1)
        if gv.option_type_2 == gv.option_type_1:
            opts_2 = opts_1
        else:
            opts_2 = get_monthly_opts(date,opts_2,gv.option_type_2)
        target_exp_1 = add_work_days(date, gv.days2exp_1)
        target_exp_2 = add_work_days(date, gv.days2exp_2)
        # --------------------------------- CLOSE ----------------------------
        basket_1_len = len(basket_1)
        basket_2_len = len(basket_2)
        del_list_1 = []
        del_list_2 = []
        day_pl_1, day_pl_2 = 0,0
        if gv.param_1:
            for i in range(basket_1_len):
                z1 = basket_1[i]
                close_routine(opts_1, date, z1, volatility, q_open)
                if z1.get_close_date() == date and z1.is_closed():
                    gv.profit_sum += z1.pos_profit()
                    gv.pl_1 += z1.pos_profit()
                    copy_z(z1, row)
                    res = res.append(row,ignore_index=True)
                    del_list_1.append(i)
                    trade_pl_1 = z1.pos_profit()
                    day_pl_1 += trade_pl_1
                    trades += 1
                    force_open_1 = True

        if gv.param_2:
            for i in range(basket_2_len):
                z2 = basket_2[i]
                close_routine(opts_2, date, z2, 0, q_open)
                if z2.get_close_date() == date and z2.is_closed():
                    gv.profit_sum += z2.pos_profit()
                    gv.pl_2 += z2.pos_profit()
                    trade_pl_2 = z2.pos_profit()
                    day_pl_2 += trade_pl_2
                    copy_z(z2,row)
                    res = res.append(row,ignore_index=True)
                    del_list_2.append(i)
                    force_open_2 = True

        max_loss = min(max_loss, day_pl_1 + day_pl_2)
        basket_1 = del_items(basket_1,del_list_1)
        if gv.param_2:
            basket_2 = del_items(basket_2,del_list_2)
        # --------------------------------- OPEN ----------------------------
        if date == last_trade_day:
            break

        parent_position = None
        if len(basket_1) < max_position_count:
            z1 = Position(gv.option_type_1, gv.side_1,primary=True)
            if gv.param_1:
                open_routine(opts_1, date, gv.algo_1, target_exp_1, z1, volatility,gv.param_1,force_open=force_open_1, basket=basket_1)
                if z1.is_open():
                    basket_1.append(z1)
                    copy_z(z1,row)
                    res = res.append(row, ignore_index=True)
                    parent_position = z1

        if len(basket_2) < max_position_count:
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
                if param_2 is not None:
                    open_routine(opts_2, date, gv.algo_2, target_exp_2, z2, volatility,param_2,force_open=force_open_2, basket=basket_2)
                if z2.is_open():
                    basket_2.append(z2)
                    copy_z(z2,row)
                    res = res.append(row, ignore_index=True)


        listz(basket_1,'eod state:')
        if gv.param_2:
            listz(basket_2,'eod state:')
