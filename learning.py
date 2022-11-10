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
    fn = '/Volumes/share/10000link.onion'
    file1 = open(fn, 'r')
    # file2 = open('/Users/oleg/today/10000link2.onion', 'a')
    file2 = open('test.onion','w')
    Lines = file1.readlines()
    # Strips the newline character
    file2.write('<html><body>\n')
    # file2.write('<a href="http://d3.ru/" target="_blank">d3</a><br>')
    c = 0

    for line in Lines:
        if line[:16] == 'http://5figq755l':
            c = c + 1
            href = line.split(' ')[0]
            newline = '<a href="%s" target="_blank">%d %s</a><br>' % (href,c,href)
            print(newline)
            file2.write(newline)
    file1.close()
    file2.write('\n</body></html>\n')
    file2.close()

def learn():
    data = pd.DataFrame({'x1': range(80, 73, - 1),  # Create pandas DataFrame
                         'x2': [1, 2, 3, 4, 5, 6, 7],
                         'x3': range(27, 20, - 1)})
    data = data.loc[(data['x1'] > 75) & (data['x1'] < 80)]
    for r,s in data.iterrows():
        c_min = 10000
        i_min = ''
        for i,c in s.items():
            if c < c_min:
                i_min = i
                c_min = c
        print(s)
        print('min: {} {}'.format(i_min,c_min))
learn()



