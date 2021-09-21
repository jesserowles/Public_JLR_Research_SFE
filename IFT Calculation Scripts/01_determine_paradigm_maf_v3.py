#calculate mean annual flow for locations in version 2 of hydrology model
import os
import sys
sys.path.insert(1, './IFT Calculation Scripts')
import pandas as pd
import numpy as np
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from get_all_sfe_lois import get_all_sfe_lois
startdir = './Reference Files/'
comids = pd.read_csv(startdir + 'SFER-POI-COMID-16Jun2020.csv',index_col = 0)
loitab, loi, fultab = get_all_sfe_lois() #full list of SFE LOIs
loipar = pd.read_excel(startdir + 'All SFE LOI Characteristics.xlsx',index_col=0) #read table to add characteristics to

for p in loi: #loop through all SFE LOIs
    if int(p) in loipar.index:
        #read unimpaired flow and calculate mean annual flow
        unimp = read_loi_paradigm_flow(p)
        loipar.loc[int(p),'Mean Annual Flow (cfs)'] = np.mean(unimp['flow'].groupby(unimp.index.year).mean())
    else: #If LOI isn't in list
        print(p + ' not valid')
loipar.loc[comids.index,'COMID']=comids['COMID'] #store COMID in the characteristics table too.
loipar.to_excel(startdir + 'All SFE LOI Characteristics with MAF.xlsx')