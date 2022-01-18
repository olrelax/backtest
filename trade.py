from datetime import datetime
from dateutil.relativedelta import relativedelta
from au import d2s,s2d,ini
from prepare_data import get_vlt, process_data, v
from os import system
# cmd = "curl -u 720adcf8-a8ea-4c87-9beb-c168a0c48e0c:suuECyYvB2Nd8egwQC9L --header 'Accept: application/json' https://api-demo.exante.eu/md/3.0/feed/SPY.ARCA/last"
# a = system(cmd)
process_data_allowed = True
def trade():
    global process_data_allowed
    process_data_allowed = False
    days2exp = ini('days2exp')
    short_dist = ini('short_dist')
    long_dist = ini('long_dist')
    date = datetime.now()
    vlt,stock = get_vlt(d2s(date))
    exp = date + relativedelta(days=days2exp)
    short_estimate = stock * (1 - short_dist / 100)
    long_estimate = stock * (1 - long_dist / 100)
    print('%s:\nexp %s\nunderlying %.2f\nshort strike %.1f\nlong strike %.1f\nvlt %.1f' % (d2s(date),d2s(exp),stock,short_estimate,long_estimate,vlt))


# trade()
