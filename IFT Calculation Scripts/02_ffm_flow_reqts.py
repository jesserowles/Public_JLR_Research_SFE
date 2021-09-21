#This calculates FFM IFTs using median dry and wet season baseflow magnitude and start time
import sys
sys.path.insert(1, './IFT Calculation Scripts')
import datetime as dt
import numpy as np
import pandas as pd
import os
from add_ts_col import add_ts_col
from get_all_sfe_lois import get_all_sfe_lois

startdir = 'IFT Results/'
loitab, loi, fultab = get_all_sfe_lois()
wyts = ['dry','moderate','wet']
ffmtable = pd.read_csv('Reference Files/FFMs_SFEel.csv')
ffmreqts = pd.DataFrame()
indexyr = 1995 # this is to be used in calculating dates of start
for l in loi:
    ffmloi = ffmtable[ffmtable['Outlet LOI'] == int(l)]
    # loiflows = pd.DataFrame(columns=['date', 'flow'])
    for wi in range(len(wyts)): #water year types
        w = wyts[wi]
        ffmloiwyt = ffmloi[ffmloi['wyt'] == w]

        #get date of season start. this should be found in a non-leap year [based on indexyr and indexyr+1]
        ds_start = dt.datetime(indexyr,10,1)+dt.timedelta(
            round(ffmloiwyt['p50'][ffmloiwyt['ffm'] == 'ds_tim'].get_values()[0]))
        ds_mag50 = ffmloiwyt['p50'][ffmloiwyt['ffm']=='ds_mag_50'].get_values()[0]

        ws_start = dt.datetime(indexyr, 10, 1) + dt.timedelta(
            round(ffmloiwyt['p50'][ffmloiwyt['ffm'] == 'wet_tim'].get_values()[0]))
        ws_mag50 = ffmloiwyt['p50'][ffmloiwyt['ffm'] == 'wet_bfl_mag_50'].get_values()[0]

        loiwytstr = l + '_' + str(wi + 1)
        ffmreqts.loc[dt.datetime(indexyr,10,1),loiwytstr] = ds_mag50
        ffmreqts.loc[ds_start, loiwytstr] = ds_mag50
        ffmreqts.loc[ws_start, loiwytstr] = ws_mag50

#fill NaNs with earliest value available
ffmreqts = ffmreqts.sort_index().fillna(method='ffill')

#add TS field for WEAP file formatting as first column
ffmreqts = add_ts_col(ffmreqts)
#save to excel
ffmreqts.to_csv(startdir + 'All LOI FFM Flow Requirements.csv')