from configparser import ConfigParser, NoOptionError
show = False
vlt_sample_size = -10
short_param = -1    # overrides short_target_price
long_param = -1
vlt_close = -10
vlt_open = -10
do_not_open_the_same_day = False
days2exp = -10
profit_sum = 0.0
profit_s = 0.0
profit_l = 0.0
stock = None
sample_len = 0
comm = 0
max_price_diff = -10
bd = ''
ed = ''
exclude_period = ''
exclude_bound = ''
suffix = ''
trade_day_of_week = None
opts_annual, opts_annual_next_year = None, None
algo_short = ''
algo_long = ''
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
short_type, long_type = '',''
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

def read_ini():
    global comm, show, vlt_close, vlt_open, do_not_open_the_same_day, days2exp, \
        short_param, long_param, vlt_sample_size, max_price_diff, bd,ed,exclude_period,trade_day_of_week, \
        algo_short, algo_long,stop_loss,forced_exit_date,intraday_tested,\
        strike_loss_limit,get_atm,cheap_limit,take_profit,abs_not_percent,atm_open_limit,atm_close_limit, \
        short_type, long_type
    abs_not_percent = ini('abs_not_percent')
    comm = ini('comm')
    show = ini('show')
    vlt_close = ini('vlt_close')
    vlt_open = ini('vlt_open')
    do_not_open_the_same_day = ini('do_not_open_the_same_day')
    days2exp = ini('days2exp')

    short_param = ini('short_param')
    long_param = ini('long_param')
    vlt_sample_size = ini('vlt_sample_size')
    max_price_diff = ini('max_price_diff')
    bd = ini('bd')
    ed = ini('ed')
    forced_exit_date = ini('forced_exit_date')
    exclude_period = ini('exclude_period')
    trade_day_of_week = ini('trade_day_of_week')
    intraday_tested = ini('intraday_tested')
    algo_short = ini('algo_short')
    algo_long = ini('algo_long')
    if algo_long is None:
        algo_long = algo_short
    stop_loss = ini('stop_loss')
    take_profit = ini('take_profit')
    strike_loss_limit = ini('strike_loss_limit')
    cheap_limit = ini('cheap_limit',False)
    get_atm = ini('get_atm',False) or algo_short == 'base_on_atm'
    atm_open_limit = ini('atm_open_limit')
    atm_close_limit = ini('atm_close_limit')
    short_type = ini('short_type')
    long_type = ini('long_type')
