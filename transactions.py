from au import d2s, s2d, intraday_tested_dates
import globalvars as gv
from datetime import datetime
from select_option import select_opt
from position import Position, getz

epoc_start = datetime.strptime('1900-01-01', '%Y-%m-%d')


def ntn(v):
    return v is not None


def close_positions(opts, date, z:Position, vlt, under_930, z_pair:Position=None):
    if z is None or not z.is_open():
        return
    is_short,  is_long = z.is_short(), z.is_long()
    option_type = z.get_option_type()
    try:
        strike = z.get_strike()
        exp = z.get_expiration()
        ret_code, opt, atm, right_strike = select_opt(opts, date, exp, expiration_mode_search='exact_date',search_value=strike,value_search_mode='exact_strike', opt_type=option_type,is_short=is_short)
    except Exception as e:
        print(e)
        atm, opt, ret_code = None, None, -1
        exit()
        if opt is None:
            if ret_code < 0:
                exit('%s: exp %s put  not found, code %d, er3' % (d2s(date), d2s(z.get_expiration()), ret_code))
            else:
                print('%s skip close, no opt history' % d2s(date))
                return
    if opt is None:
        if date == z.get_expiration():
            exit('option %s expired at %s strike %.2f not found' % (z.get_option_type(),d2s(z.get_expiration()),z.get_strike()))
        else:
            return
    opt_high = opt['high']
    opt_low = opt['low']
    opt_930 = opt['open']
    opt_1545 = opt['ask_1545'] if is_short else opt['bid_1545']
    under_1545 = opt['underlying_bid_1545'] if is_short else opt['underlying_ask_1545']
    expired_criteria = date == z.get_expiration()
    vlt_criteria = vlt > gv.vlt_close if ntn(gv.vlt_close) and option_type == 'P' else False
    exclude_period_criteria = s2d(gv.exclude_bound[0]) <= date < s2d(gv.exclude_bound[1]) if ntn(gv.exclude_bound) else False
    date_criteria = exclude_period_criteria or date == s2d(gv.ed)
    strike_loss_limit_criteria_930 = is_short and ntn(gv.strike_loss_limit) and under_930 < z.get_strike() - gv.strike_loss_limit
    strike_loss_limit_criteria_1545 = is_short and ntn(gv.strike_loss_limit) and under_1545 < z.get_strike() - gv.strike_loss_limit
    stop_loss_criteria = is_short and ntn(gv.stop_loss) and opt_high > gv.stop_loss
    take_profit_criteria = is_short and ntn(gv.take_profit) and opt_low < gv.take_profit
    atm_limit_criteria_930 = is_short and gv.get_atm and ntn(gv.atm_close_limit) and atm['open'] > gv.atm_close_limit
    atm_limit_criteria_1545 = is_short and gv.get_atm and ntn(gv.atm_close_limit) and atm['bid_1545'] > gv.atm_close_limit

    close_time = None
    closing_reason = None
    close_price = None
    if strike_loss_limit_criteria_930:
        close_price = opt_930
        closing_reason = 'StrikeLoss930'
        close_time = 930
    elif strike_loss_limit_criteria_1545:
        close_price = opt_1545
        closing_reason = 'StrikeLoss930'
        close_time = 1545
    elif atm_limit_criteria_930:
        z.atm = atm['open']
        close_price = opt['open']
        closing_reason = 'AtmLimit_930'
        close_time = 930
    elif atm_limit_criteria_1545:
        z.atm = atm['bid_1545']
        close_price = opt['bid_1545']
        closing_reason = 'AtmLimit_1545'
        close_time = 1545
    elif stop_loss_criteria:
        intra = intraday_tested_dates(date)
        if intra:
            close_price = gv.stop_loss * 1.03
        else:
            close_price = opt_high
        closing_reason = 'StopLoss'
        close_time = 1545
    elif take_profit_criteria:
        closing_reason = 'TakeProfit'
        close_price = opt_low
        close_time = 1545
    elif expired_criteria:
        field = 'bid_eod' if is_long else 'ask_eod'
        under_field = 'underlying_bid_eod' if is_short else 'underlying_ask_eod'
        stock_above_strike = opt[under_field] - opt['strike']
        if option_type == 'P':
            close_price = opt[field] if stock_above_strike < 0 else 0.0
        elif option_type == 'C':
            close_price = opt[field] if stock_above_strike > 0 else 0.0
        closing_reason = 'Expired'
        close_time = 1600
    elif vlt_criteria:
        close_price = opt['bid_1545'] if z.is_long() else opt['ask_1545']
        closing_reason = 'Forced_vlt'
        close_time = 1545
    elif date_criteria:
        close_price = opt['bid_1545'] if z.is_long() else opt['ask_1545']
        closing_reason = 'Forced_date'
        close_time = 1600
    elif ntn(z_pair) and z_pair.call_pair_close > 0:
        if z_pair.close_time == 1600:
            close_price = opt['bid_eod'] if z.is_long() else opt['ask_eod']
            close_time = 1600
            closing_reason = 'Forced_pair_1600'
        elif z_pair.close_time == 930:
            close_price = opt['open']
            close_time = 930
            closing_reason = 'Forced_pair_930'
        elif z_pair.close_time == 1545:
            close_price = opt['open']
            close_time = 1545
            closing_reason = 'Forced_pair_930'
    else:
        return
    if close_time is None or closing_reason is None or close_price is None:
        exit('bug here')
    z.comment = closing_reason + 'S' if z.is_short() else closing_reason + 'L'
    z.comment = z.comment + option_type
    z.underlying = under_1545
    z.close_position(close_price, date, closing_reason, close_time)
    z.info(prefix='closing:')


SHORT = -1
LONG = 1

def check_trade_days(date):
    if gv.trade_day_of_week is None:
        return True
    if isinstance(gv.trade_day_of_week,int):
        return date.isoweekday() == gv.trade_day_of_week
    elif isinstance(gv.trade_day_of_week,str):
        days_list = list(map(int, gv.trade_day_of_week.split(',')))
        return date.isoweekday() in days_list

def open_position(opts, date: datetime, algo, target_exp, basket, z: Position, vlt, param):
    if not z.is_tradable():
        return
    is_short, is_long = z.is_short(), z.is_long()
    option_type = z.get_option_type()
    vlt_open_criteria = vlt < gv.vlt_open if ntn(gv.vlt_open) and z.get_option_type == 'P' else vlt > gv.vlt_open if ntn(
        gv.vlt_open) and z.get_option_type == 'C' else True
    exclude_date_criteria = s2d(gv.exclude_bound[0]) <= date < s2d(gv.exclude_bound[1]) if gv.exclude_bound is not None else False
    weekday_criteria = check_trade_days(date)
    day_criteria = weekday_criteria
    forced = date == s2d(gv.forced_exit_date)

    if algo in ('base_on_atm', 'nn', 'distance', 'hedge_distance','hedge_discount', 'fixprice'):
        open_criteria = not z.is_open() and not forced and vlt_open_criteria and day_criteria and not exclude_date_criteria
    elif algo == 'get_right_atm':
        open_criteria = is_short
    else:
        open_criteria = None
    if open_criteria:
        if z.closing_reason == 'v':
            if z.get_close_date() == date and gv.do_not_open_the_same_day:
                return
        ret_code, opt, atm_row, right_strike = select_opt(opts, date, target_exp,  expiration_mode_search='closest_date', search_value=param, value_search_mode=algo, opt_type=option_type, is_short=is_short)

        if opt is None:
            if ret_code < 0:
                exit('%s: exp %s %s opt for open not found, code %d, er6' % (
                    d2s(date), d2s(target_exp), z.get_option_type, ret_code))
            else:
                print('%s skip, no opts hist' % d2s(date))
                return
        exp = opt['expiration']
        if exp > s2d(gv.ed):
            return
        atm = atm_row['bid_1545'] if atm_row is not None else None
        if basket is not None and getz(basket, exp) is not None:
            return
        strike = opt['strike']
        price_1545 = opt['bid_1545'] if z.is_short() else opt['ask_1545']
        under = opt['underlying_ask_1545']
        if gv.cheap_limit and is_short and price_1545 < gv.cheap_limit:
            return
        if gv.get_atm and gv.atm_open_limit is not None and atm > gv.atm_open_limit:
            return

        z.open_position(date, exp, strike, price_1545)
        z.comment = 'OpenS' if z.is_short() else 'OpenL'
        z.comment = z.comment + option_type

        z.underlying = under
        z.right_strike = right_strike
        z.atm = atm
        z.info(prefix='opening:')
    return
