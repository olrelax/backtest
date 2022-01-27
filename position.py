from datetime import datetime
import globalvars as gv
def d2s(dtm,fmt='%Y-%m-%d'):
    return datetime.strftime(dtm,fmt)
def s2d(text,fmt='%Y-%m-%d'):
    return datetime.strptime(text,fmt)


class Position:
    def __init__(self, opt_type, short_long,primary=False):
        self.__option_type = opt_type
        self.__opt_type_sign = -1 if opt_type == 'P' else 1
        self.__strike = 0.
        self.__side = -1 if short_long == 'S' else 1 if short_long == 'L' else 0
        self.__open_close_switch = 0
        self.__enter_price = 0.
        self.__current_price = 0.
        self.__expiration = gv.epoc_start
        self.__open_date = gv.epoc_start
        self.__close_date = gv.epoc_start
        self.closing_reason = ''
        self.comment = ''
        self.close_commission = 0.
        self.underlying = 0
        self.right_strike = 0
        self.atm = 0
        self.close_time = None
        self.__last_transaction_date = gv.epoc_start
        self.is_primary = primary
    def option_type(self):
        return self.__option_type
    def enter_price(self):
        return self.__enter_price
    def strike(self):
        return self.__strike
    def expiration(self):
        return self.__expiration
    def is_tradable(self):
        return abs(self.__side) > 0
    def is_open(self):
        return self.__open_close_switch == 1
    def is_closed(self):
        return self.__open_close_switch == 0
    def is_short(self):
        return self.__side < 0
    def is_long(self):
        return self.__side > 0
    def side(self):
        return self.__side
    def close_date(self):
        return self.__close_date
    def open_date(self):
        return self.__open_date
    def last_transaction_date(self):
        return self.__last_transaction_date
    def set_current(self,price):
        self.__current_price = price
    def current(self):
        return self.__current_price
    def margin(self):
        return (self.__current_price - self.__enter_price) * self.__side
    def value(self):
        return self.__current_price * self.__open_close_switch * self.__side


    def info(self,print_it=True,prefix=''):
        side = 'S' if self.is_short() else 'L' if self.is_long() else'Undef'

        if self.is_open():
            state = '%s %s open_date %s, expiration %s, strike %.1f, premium %.2f, is open' % (self.__option_type,side, d2s(self.__open_date),d2s(self.__expiration),self.__strike,self.__enter_price)
        elif self.is_closed():
            state = '%s %s open_date %s, expiration %s, strike %.1f, premium %.2f, closed %s, close price %.2f' %\
                    (self.__option_type,side, d2s(self.__open_date),d2s(self.__expiration),self.__strike,self.__enter_price,
                     d2s(self.__close_date),self.__current_price)
        else:
            state = 'not set'
        info = '%s %s' % (prefix,state)
        if print_it:
            print(info)
        return info


    def open_position(self, date, expiration, strike, premium):

        exp = s2d(expiration) if isinstance(expiration,str) else expiration
        dt = s2d(date) if isinstance(date,str) else date
        if self.is_open():
            exit('%s %s strike %.1f already open' % (d2s(exp), self.__option_type, strike))
        self.__open_close_switch = 1
        self.__strike = strike
        self.__expiration = exp
        self.__enter_price = premium
        self.__current_price = premium
        self.__open_date = dt
        self.__last_transaction_date = date
        return 1

    def close_position(self, curr_opt_price,date,closing_reason,close_time,under):
        dt = s2d(date) if isinstance(date,str) else date
        if self.is_open():
            self.__open_close_switch = -1
            self.__current_price = curr_opt_price
            self.__close_date = dt
            self.closing_reason = closing_reason
            itm = (under - self.__strike) * self.__opt_type_sign > 0
            self.close_commission = gv.comm if itm or not self.closing_reason[:3] == 'Exp' else 0.
            self.close_time = close_time
            self.__open_close_switch = 0
            self.__last_transaction_date = date
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

