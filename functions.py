from au import read_opt_file
import inspect
def from_d1_subtract_d2(d1,d2,cols):
    idx = d1[cols].isin(d2[cols])
    idx1 = idx[cols[0]] & idx[cols[1]]
    return d1.loc[~idx1]

def get_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def show(df,stop=True):
    name = get_name(df)[0]
    print('-----------------%s------------' % name)
    #print(df.info())
    print(df.columns.tolist())
    if stop:
        exit()
def save(dtf,arg_name=None,stop=False):
    name = get_name(dtf)[0] if arg_name is None else arg_name
    print('save',name)
    dtf.to_csv('../devel/%s.csv' % name,index=True)
    if stop:
        exit()
def get_strike_loss(df,i,field,strike_loss_limit):
    df_loss = df.copy()
    # df_loss['str_loss_%d' % i] = df_loss['strike_%d' % i] - df_loss['under_bid_in_%d' % i]
    df_loss['str_loss_%d' % i] = df_loss['strike_%d' % i] - df_loss['%s_%d' % (field,i)]
    df_loss = df_loss.loc[df_loss['str_loss_%d' % i] > strike_loss_limit]
    df_loss = df_loss.drop_duplicates(subset=['expiration'])

    return df_loss

def get_df_between_1(df_in2exp,side,tp,i,strike_loss_limit):
    side_sign = 1. if side == 'S' else -1.
    df_in2exp['pair_in'] = df_in2exp['quote_date'].astype(str)+df_in2exp['expiration'].astype(str)
    df_all = read_opt_file('../data/SPY_CBOE_2020-2022_%s.csv' % tp)
    df_all = df_all.loc[df_all.days_to_exp < 8]

    df_all = df_all.rename(columns={'strike':'strike_%d' % i})
    df_in2exp2exclude = df_in2exp[['quote_date','expiration','strike_%d' % i,'pair_in']]   # list of contracts ended at expiration
    df_mix = df_all.merge(df_in2exp2exclude,on=['expiration','strike_%d' % i])
    df_between = df_mix.loc[~(df_mix['quote_date_x'] == df_mix['quote_date_y'])]
    df_between = df_between.loc[~(df_between['quote_date_x'] == df_between['expiration'])]
    df_between = df_between.rename(
        columns={'quote_date_x':'quote_date', 'underlying_bid_1545': 'under_bid_out_%d' % i,'underlying_ask_1545': 'under_ask_out_%d' % i,
                 'bid_1545': 'bid_out_%d' % i,'ask_1545': 'ask_out_%d' % i})
    df_between = df_between[['quote_date', 'expiration', 'strike_0','bid_out_0', 'ask_out_0', 'under_bid_out_0', 'under_ask_out_0', 'bid_eod', 'ask_eod', 'underlying_bid_eod', 'underlying_ask_eod']]
    df_between['exit_date'] = df_between['quote_date']
    df_between['under_bid_in_%d' % i] = df_between['under_bid_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    df_between['under_ask_in_%d' % i] = df_between['under_ask_out_%d' % i]         # just mirroring for compatibility with df_in2exp
#    show(df_between,False)

    # The quote_date in this df is the date of exit due to loss limit, so prices on that date is the out prices.
    # To calculate loss margin we join df_in2exp to get prices at the date of enter:
    df_between = df_between.merge(df_in2exp[['quote_date','expiration','strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i]],on=['expiration','strike_%d' % i])
    df_between = df_between.rename(columns={'quote_date_x':'quote_date','quote_date_y':'enter_date'})
    df_between = df_between[['quote_date','expiration','enter_date','exit_date','strike_%d' % i,'under_bid_in_%d' % i,'under_ask_in_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,
                             'under_bid_out_%d' % i,'under_ask_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i]]
    df_between['margin_%d' % i] = (df_between['bid_in_%d' % i] - df_between['ask_out_%d' % i]) * side_sign
    df_between = get_strike_loss(df_between,i,'under_bid_in',strike_loss_limit)
    return df_between




def get_df_between_0(df_in2exp,side,tp,i):
    side_sign = 1. if side == 'S' else -1.
    df_in2exp['pair_in'] = df_in2exp['quote_date'].astype(str)+df_in2exp['expiration'].astype(str)
    df_all = read_opt_file('../data/SPY_CBOE_2020-2022_%s.csv' % tp)
    df_all = df_all.loc[df_all.days_to_exp < 8]

    df_all = df_all.rename(columns={'strike':'strike_%d' % i})
    df_in2exp2exclude = df_in2exp[['quote_date','expiration','strike_%d' % i,'pair_in']]   # list of contacts lasted till on expiration
    df_mix = df_all.merge(df_in2exp2exclude,on=['expiration','strike_%d' % i])
    df_between = df_mix[(~df_mix.pair_all.isin(df_in2exp2exclude.pair_in))]
    df_between = df_between.loc[~(df_between['quote_date_x'] == df_between['expiration'])]
    df_between = df_between.rename(
        columns={'quote_date_x':'quote_date', 'underlying_bid_1545': 'under_bid_out_%d' % i,'underlying_ask_1545': 'under_ask_out_%d' % i,
                 'bid_1545': 'bid_out_%d' % i,'ask_1545': 'ask_out_%d' % i})
    df_between['under_bid_in_%d' % i] = df_between['under_bid_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    df_between['under_ask_in_%d' % i] = df_between['under_ask_out_%d' % i]         # just mirroring for compatibility with df_in2exp
    # The quote_date in this df is the date of exit due to loss limit, so prices on that date is the out prices.
    # To calculate loss margin we join df_in2exp to get prices at the date of enter
    df_between = df_between.merge(df_in2exp[['expiration','strike_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i]],on=['expiration','strike_%d' % i])
    df_between = df_between[['quote_date','expiration','strike_%d' % i,'under_bid_in_%d' % i,'under_ask_in_%d' % i,'bid_in_%d' % i,'ask_in_%d' % i,
                             'under_bid_out_%d' % i,'under_ask_out_%d' % i,'bid_out_%d' % i,'ask_out_%d' % i]]
    df_between['margin_%d' % i] = (df_between['bid_in_%d' % i] - df_between['ask_out_%d' % i]) * side_sign
    df_between = get_strike_loss(df_between,i,'under_bid_in',strike_loss_limit)
    return df_between

