from configparser import ConfigParser, NoOptionError
# cash = 0
# portfolio = 0
# real_sum_1 = 0.0
# real_sum_2 = 0.0
# real_sum_and_curr_pl_1 = 0.0
# real_sum_and_curr_pl_2 = 0.0
show = False
param_1 = None
param_2 = None
vlt_close = -10
vlt_open = -10
days2exp_1 = -10
days2exp_2 = -10
# profit_sum = 0.0
stock = None
sample_len = 0
comm = 0.021
bd = ''
ed = ''
exclude_period = ''
exclude_bound = ''
suffix = ''
trade_day_of_week_1 = None
trade_day_of_week_2 = None
opts_annual_C, opts_annual_next_year_C = None, None
opts_annual_P, opts_annual_next_year_P = None, None
algo_1 = ''
algo_2 = ''
stop_loss = None
take_profit = None
config_object = None
cheap_limit = None
forced_exit_date = ''
intraday_tested = ''
strike_loss_limit = 0
get_atm = False
abs_not_percent = True
atm_open_limit, atm_close_limit = 0, 0
option_type_1, option_type_2 = '',''
side_1, side_2 = '',''
current_month = 0
epoc_start = None
def reset_test():
    global current_month,opts_annual_C, opts_annual_next_year_C,opts_annual_P, opts_annual_next_year_P
    current_month = 0
    opts_annual_C,opts_annual_next_year_C, opts_annual_P, opts_annual_next_year_P = None, None, None, None

def is_float(s):
    try:
        float(s)
        return not s.isdigit()
    except ValueError:
        return False
def prn(text, color=''):
    if color == 'red':
        print('\033[31m' + text + '\033[0m')
    elif color == 'green':
        print('\033[32m' + text + '\033[0m')
    elif color == 'yellow':
        print('\033[33m' + text + '\033[0m')
    elif color == 'blue':
        print('\033[34m' + text + '\033[0m')
    elif color == 'magenta':
        print('\033[35' + text + '\033[0m')
    elif color == 'cyan':
        print('\033[36m' + text + '\033[0m')
    elif color == 'white':
        print('\033[37m' + text + '\033[0m')
    else:
        print(text)


def set_config_object():
    global config_object
    config_object = ConfigParser()
    config_object.read('config.ini')
    return config_object

def ini(entry_name, default_value=None):
    section = 'parameters'
    global config_object
    try:
        if config_object is None:
            config_object = set_config_object()
        parser = config_object
        a = parser.get(section, entry_name)
        comment_start = a.find('#')
        if comment_start >= 0:
            a = a[:comment_start].rstrip()
        else:
            a = a.rstrip()
        if a in ('True', 'False'):
            if a == 'True':
                return True
            else:
                return False
        elif is_float(a):
            return float(a)
        elif a.isdigit():
            return int(a)
        elif len(a) > 0:
            return a
        else:
            return default_value
    except ValueError:
        prn('ValueError: %s' % entry_name,'red')
        return default_value
    except NoOptionError:
        prn('no option: %s return default value' % entry_name,'yellow')
        return default_value
def trade_scheme(ini_str):
    trade_scheme_list = list(map(lambda x:x.split('='),ini_str.split(',')))
    weekdays = trade_scheme_list[0][1]
    weekdays = list(map(int,weekdays)) if len(weekdays) > 1 else int(weekdays) if len(weekdays) > 0 else 0
    expiration_term = trade_scheme_list[1][1]
    if len(expiration_term) == 0:
        days_to_expiration = 0
    elif expiration_term[-1:] == 'w':
        days_to_expiration = int(expiration_term[:-1]) * 5
    elif expiration_term[-1:] == 'm':
        days_to_expiration = int(expiration_term[:-1]) * 20
    else:
        days_to_expiration = int(expiration_term)
    if weekdays == 0:
        if days_to_expiration > 0:
            exit('wrong scheme %s. Unset expiration' % ini_str)
    elif days_to_expiration % 5 > 0:
        exit('wrong scheme %s' % ini_str)
    return weekdays,days_to_expiration

def read_ini():
    global comm, show, vlt_close, vlt_open, days2exp_1,days2exp_2, \
        param_1, param_2, bd,ed,exclude_period,trade_day_of_week_1,trade_day_of_week_2,  \
        algo_1, algo_2,stop_loss,forced_exit_date,intraday_tested,\
        strike_loss_limit,get_atm,cheap_limit,take_profit,abs_not_percent,atm_open_limit,atm_close_limit, \
        option_type_1, option_type_2,side_1,side_2
    abs_not_percent = ini('abs_not_percent')
    comm = ini('comm')
    show = ini('show')
    vlt_close = ini('vlt_close')
    vlt_open = ini('vlt_open')

    param_1 = ini('param_1')
    param_2 = ini('param_2')
    bd = ini('bd')
    ed = ini('ed')
    forced_exit_date = ini('forced_exit_date')
    exclude_period = ini('exclude_period')
    trade_scheme_1 = ini('trade_scheme_1')
    trade_scheme_2 = ini('trade_scheme_2')
    trade_day_of_week_1,days2exp_1 = trade_scheme(trade_scheme_1)
    trade_day_of_week_2,days2exp_2 = trade_scheme(trade_scheme_2)
    intraday_tested = ini('intraday_tested')
    algo_1 = ini('algo_1')
    algo_2 = ini('algo_2')
    if algo_1 is None:
        algo_2 = algo_1
    stop_loss = ini('stop_loss')
    take_profit = ini('take_profit')
    strike_loss_limit = ini('strike_loss_limit')
    cheap_limit = ini('cheap_limit',False)
    get_atm = ini('get_atm',False) or algo_1 == 'base_on_atm'
    atm_open_limit = ini('atm_open_limit')
    atm_close_limit = ini('atm_close_limit')
    option_type_1 = ini('option_type_1')
    option_type_2 = ini('option_type_2')
    side_1 = ini('side_1')
    side_2 = ini('side_2')
    if algo_2[:5] == 'hedge':
        if not trade_day_of_week_1 == trade_day_of_week_2 or not days2exp_1 == days2exp_2:
            exit('trading scheme must be equal for hedging')
