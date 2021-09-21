import sys
sys.path.insert(1, './IFT Calculation Scripts')
import pandas as pd
import datetime as dt
import numpy as np
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from get_all_sfe_lois import get_all_sfe_lois
from add_ts_col import add_ts_col

startdir = 'IFT Results/'
loitab, loi, fultab = get_all_sfe_lois()
loitab = fultab
alldates = pd.date_range(dt.datetime(1995,10,1),dt.datetime(2017,9,30))
dailyreqts = pd.DataFrame(index=alldates,columns=loi)  #set up IFT table for WEAP
loitab['NCIFP MBF'] = np.zeros_like(loitab['MAF']) #initialize minimum bypass flow metric
for l in loi: #loop through lcoations
    loimaf = loitab.loc[int(l),'MAF'] #extract LOI mean annual flow
    loicta = loitab.loc[int(l),'Contributing Area (mi^2)'] #extract LOI contributing area
    loiqbf = loitab.loc[int(l),'Qbf'] #extract LOI bankfull flow
    loistr = l
    unimp = read_loi_paradigm_flow(loistr)
    #NCIFP calculations based on bin of Contributing area
    if loicta <= 1:
        loimbf = 9 * loimaf
    elif (loicta > 1) & (loicta < 321):
        loimbf = 8.8 * loimaf * loicta ** -0.47
    else:
        loimbf = 0.6 * loimaf
    loidiv = loiqbf*0.05 #diversion allocation is 5% of bankfull
    loitab.loc[int(l),'NCIFP MBF'] = loimbf #record MBF
    unimp['NCIFP div aloc'] = np.zeros_like(unimp['flow'])
    unimp['flow above mbf'] = unimp['flow']-loimbf #calculate flow above MBF
    unimp.loc[unimp['flow above mbf']>loidiv,'flow above mbf'] = loidiv #allow full diversion amount when there is more than enough flow to divert
    #get index of diversion period
    divinds = (unimp['flow'] > loimbf) & ((unimp.index.month <= 3) | ((unimp.index.day >= 15) & (unimp.index.month == 12)))
    unimp.loc[divinds,'NCIFP div aloc'] = unimp.loc[divinds,'flow above mbf'] #loidiv
    unimp['NCIFP flow req'] = unimp['flow'] - unimp['NCIFP div aloc'] #IFT = flow - diversion
    dailyreqts.loc[:,loistr] = unimp.loc[dailyreqts.index,'NCIFP flow req'].fillna(value=0)
dailyreqts = add_ts_col(dailyreqts)
dailyreqts.to_csv(startdir + 'All LOI NCIFP IFTs.csv')


