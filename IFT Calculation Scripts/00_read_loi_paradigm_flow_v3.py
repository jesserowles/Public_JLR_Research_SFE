#this function is used in most scripts. It reads in unimpaired flow for a given location and returns it
# as a dataframe.
import os
import pandas as pd
import datetime as dt

def read_loi_paradigm_flow(p):
    unimpath = './Unimpaired Flow/'
    unimpflowfile = unimpath + p + '.csv'
    unimp = pd.read_csv(unimpflowfile,index_col=0)
    unimp.index = pd.DatetimeIndex(unimp.index)
    return unimp
