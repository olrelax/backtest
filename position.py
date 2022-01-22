from datetime import datetime
import globalvars as gv
def d2s(dtm,fmt='%Y-%m-%d'):
    return datetime.strftime(dtm,fmt)
def s2d(text,fmt='%Y-%m-%d'):
    return datetime.strptime(text,fmt)

epoch_begin = datetime.strptime('1000-01-01', '%Y-%m-%d')

class Position:
    def __init__(self, opt_type, short_long,primary=False,call_pair_close=False):
        self.__option_type = opt_type
        self.__strike = 0.
        self.__side = -1 if short_long == 'S' else 1 if short_long == 'L' else 0
        self.__open_close_switch = 0
        self.__enter_price = 0.
        self.__last_price = 0.
        self.__expiration = epoch_begin
        self.__open_date = epoch_begin
        self.__close_date = epoch_begin
        self.closing_reason = ''
        self.comment = ''
        self.commission = 0.
        self.underlying = 0
        self.right_strike = 0
        self.atm = 0
        self.close_time = None
        self.call_pair_close = call_pair_close
        self.is_primary = primary
    def get_option_type(self):
        return self.__option_type
    def get_enter_price(self):
        return self.__enter_price
    def get_strike(self):
        return self.__strike
    def get_last_price(self):
        return self.__last_price
    def get_expiration(self):
        return self.__expiration
    def is_tradable(self):
        return abs(self.__side) > 0
    def is_open(self):
        return self.__open_close_switch > 0
    def is_closed(self):
        return self.__open_close_switch < 0
    def is_virgin(self):
        return self.__open_close_switch == 0
    def is_short(self):
        return self.__side < 0
    def is_long(self):
        return self.__side > 0
    def get_side(self):
        return self.__side
    def get_close_date(self):
        return self.__close_date
    def get_open_date(self):
        return self.__open_date


    def info(self,print_it=True,prefix=''):
        side = 'S' if self.is_short() else 'L' if self.is_long() else'Undef'

        if self.is_open():
            state = '%s %s open_date %s, expiration %s, strike %.1f, premium %.2f, is open' % (self.__option_type,side, d2s(self.__open_date),d2s(self.__expiration),self.__strike,self.__enter_price)
        elif self.is_closed():
            state = '%s %s open_date %s, expiration %s, strike %.1f, premium %.2f, closed %s, close price %.2f' %\
                    (self.__option_type,side, d2s(self.__open_date),d2s(self.__expiration),self.__strike,self.__enter_price,
                     d2s(self.__close_date),self.__last_price)
        else:
            state = 'not set'
        info = '%s %s' % (prefix,state)
        if print_it:
            print(info)
        return info

    def pos_profit(self):
        return (self.__last_price - self.__enter_price) * self.__side - self.commission

    def pos_margin(self):
        return (self.__last_price - self.__enter_price) * self.__side

    def open_position(self, date, expiration, strike, premium):

        exp = s2d(expiration) if isinstance(expiration,str) else expiration
        dt = s2d(date) if isinstance(date,str) else date
        if self.is_open():
            exit('%s %s strike %.1f already open' % (d2s(exp), self.__option_type, strike))
        self.__open_close_switch = 1
        self.__strike = strike
        self.__expiration = exp
        self.__enter_price = premium
        self.__last_price = premium
        self.__open_date = dt
        self.commission = gv.comm
        return 1

    def close_position(self, curr_opt_price,date,closing_reason,close_time):
        dt = s2d(date) if isinstance(date,str) else date
        if self.is_open():
            self.__open_close_switch = -1
            self.__last_price = curr_opt_price
            self.__close_date = dt
            self.closing_reason = closing_reason
            self.commission = self.commission + gv.comm if not self.closing_reason[:3] == 'Exp' else self.commission
            self.close_time = close_time
        else:
            exit('closing zero position')


def getz(arr: [Position],date):
    exp = s2d(date) if isinstance(date, str) else date
    for pz in arr:
        if pz.get_expiration() == exp:
            return pz

def delzd(arr: [Position],date):
    exp = s2d(date) if isinstance(date, str) else date
    idx = 0
    for pz in arr:
        if pz.get_expiration() == exp:
            arr.pop(idx)
            return arr
        idx += 1
    return arr

def delz(arr, poz):
    idx = 0
    for pz in arr:
        if pz is poz:
            arr.pop(idx)
            return arr
        idx += 1
    return arr


def listz(arr,txt=''):
    for pz in arr:
        pz.info(prefix=txt)

if __name__ == '__main__':
    za = []
    z = Position('P', -1)
    z.open_position('2020-01-01','2020-01-07',333,0.5)
    za.append(z)
    z = Position('P', -1)
    z.open_position('2020-01-02','2020-01-08',303,0.34)
    za.append(z)
    z = Position('P', -1)
    z.open_position('2020-01-03','2020-01-09',304,0.34)
    za.append(z)
    z = Position('P', -1)
    z.open_position('2020-01-06','2020-01-13',305,0.34)
    za.append(z)
    z = Position('P', -1)
    z.open_position('2020-01-07','2020-01-14',305,0.34)
    za.append(z)

    del_list = [1,2]
    zb = []
    zl = len(za)
    for i in range(zl):
        if i not in del_list:
            zb.append(za[i])
    print('za:')
    listz(za)
    print('zb:')
    listz(zb)
    za = zb
    print('za:')
    listz(za)

