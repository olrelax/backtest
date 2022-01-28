import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import au
from au import s2d,fl,d2s,add_days, add_work_days
from inspect import currentframe, getframeinfo
import matplotlib.pyplot as plt
from os import system
from position import Position
from datetime import datetime
import time
import sqlitetocsv as sql
import globalvars as gv

from inspect import currentframe, getframeinfo
from au import fl
import sftpclient as cl
def learn():
    c = cl.SFTPClient('sftp.datashop.livevol.com','olrelax_gmail_com','Hiwiehi0fz1$',False)
    c.download('subscriptions/order_000025299/item_000030286/UnderlyingOptionsEODQuotes_2021-12-27.zip')


learn()
