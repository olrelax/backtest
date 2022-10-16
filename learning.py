import pandas as pd
from dateutil.relativedelta import *
from au import read_entry
import numpy as np
import csv
from datetime import datetime
import time
import urllib.request
import urllib.error
from io import StringIO
import ssl
# US1.QQQ_190901_220930
def finam():
    df = pd.read_csv('../data/FINAM/US1.QQQ_190901_220930.csv',usecols=['<DATE>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>'],dtype={'<DATE>':str,'<TIME>':str})
    df['Date'] = pd.to_datetime(df['<DATE>'].astype(str)+'-'+df['<TIME>'].astype(str),format='%Y%m%d-%H%M%S')
    print(df.head())
    df = df[['Date','<DATE>','<OPEN>','<HIGH>','<LOW>','<CLOSE>']]
    dfo = df.loc[df['Date'].dt.hour == 13][['Date','<DATE>','<OPEN>']]
    dfc = df.loc[df['Date'].dt.hour == 15][['<DATE>','<CLOSE>']]
    dfm = pd.merge(dfo,dfc,on='<DATE>')
    dfm['dd_usd'] = dfm['<OPEN>'] - dfm['<CLOSE>']
    dfm['dd_prc'] = 100.0*(dfm['dd_usd']/dfm['<OPEN>'])
    dfm = dfm.sort_values('dd_prc')
    print(dfm.tail(5))
finam()

