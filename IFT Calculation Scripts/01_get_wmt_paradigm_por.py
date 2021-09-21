#calculate WMTs at each location
import datetime as dt
import numpy as np
import pandas as pd
import os
import sys
sys.path.insert(1, './IFT Calculation Scripts')
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from get_all_sfe_lois import get_all_sfe_lois

sublois, loi, sfelois = get_all_sfe_lois()

for l in loi:
    unimp = read_loi_paradigm_flow(l)
    mmflow = unimp.resample('1M').mean() #calculate resampled unimpaired mean monthly flows
    mmflow['Month'] = mmflow.index.month
    mmflow['Year'] = mmflow.index.year
    mmflow = mmflow[['Month','Year','flow']]
    mmflow['WMT'] = ''
    for m in range(1,13): #loop through each calendar month
        singlemmflow = mmflow[mmflow.index.month == m] #filter to calendar months
        #calculate WMT from percentiles
        edth = singlemmflow['flow'].quantile(0.1)
        dyth = singlemmflow['flow'].quantile(0.3)
        bmth = singlemmflow['flow'].quantile(0.5)
        amth = singlemmflow['flow'].quantile(0.7)
        wtth = singlemmflow['flow'].quantile(0.9)
        mmflow.loc[singlemmflow[singlemmflow['flow'] < edth].index,'WMT'] = 'Critically Dry'
        mmflow.loc[singlemmflow[(singlemmflow['flow'] >= edth) & (singlemmflow['flow'] < dyth)].index,'WMT'] = 'Dry'
        mmflow.loc[singlemmflow[(singlemmflow['flow'] >= dyth) & (singlemmflow['flow'] < bmth)].index,'WMT'] = 'Below Median'
        mmflow.loc[singlemmflow[(singlemmflow['flow'] >= bmth) & (singlemmflow['flow'] < amth)].index,'WMT'] = 'Above Median'
        mmflow.loc[singlemmflow[(singlemmflow['flow'] >= amth) & (singlemmflow['flow'] < wtth)].index,'WMT'] = 'Wet'
        mmflow.loc[singlemmflow[singlemmflow['flow'] >= wtth].index,'WMT'] = 'Extremely Wet'
    mmflow.index = mmflow.index.strftime('%b-%Y')
    mmflow.to_excel('./Unimpaired Flow/Water Month Types/LOI ' + l + ' WMT.xlsx')