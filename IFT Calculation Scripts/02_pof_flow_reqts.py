#Calculate POF IFTs, only for plotting/reference. Ones used in WEAP are calculated in WEAP
import sys
sys.path.insert(1, './IFT Calculation Scripts')
import datetime as dt
import numpy as np
import pandas as pd
import os
from add_ts_col import add_ts_col
from get_all_sfe_lois import get_all_sfe_lois
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow

startdir = 'IFT Results/'
loitab, loi, fultab = get_all_sfe_lois()
pcts = [0.75,0.8,0.9,0.95] #set of POFs, defaults are 75%, 80%, 90%, 95%
for p in pcts:
    pofreqts = pd.DataFrame(columns=loi)
    for i in loi:
        unimp = read_loi_paradigm_flow(i)
        pofreqts[i] = unimp['flow']*p
    pofreqts = add_ts_col(pofreqts)
    pofreqts.to_csv(startdir + 'All LOI POF ' + str(int(p * 100)) + '% IFTs.csv')
    print(str(int(p*100)) + '% finished')
