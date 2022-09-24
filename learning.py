import pandas as pd
from dateutil.relativedelta import *
from au import read_entry
import numpy as np
import csv

a = read_entry('prepare','arg3')
print(type(a), '-%s-' % a)
