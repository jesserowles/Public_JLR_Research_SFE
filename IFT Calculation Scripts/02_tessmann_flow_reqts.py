#Calculate Tessmann IFTs. Mostly just reading them from provided table and formatting for WEAP
import sys
sys.path.insert(1, './IFT Calculation Scripts')
import pandas as pd
import datetime as dt
import numpy as np
from add_ts_col import add_ts_col
from get_all_sfe_lois import get_all_sfe_lois

startdir = 'IFT Results/'
tesreqtsfile = 'Reference Files/Tessmann_min_flows_SWB.csv' #provided Tessmann table
tesreqts = pd.read_csv(tesreqtsfile)

loitab, loi, fultab = get_all_sfe_lois()

startdate = dt.datetime(1995,10,1)
enddate = dt.datetime(1996,9,30)
alldates = pd.date_range(startdate,enddate, freq='MS')
dailyreqts = pd.DataFrame(index=alldates)
month = range(1,13)
for i in loitab['Outlet LOI']:
    setzero = 0
    comid = int(loitab['COMID'][loitab['Outlet LOI']==i].get_values()[0]) #get COMID
    if comid == -99: #LOI has no COMID
        print('COMID = ' +str(int(comid)) + ' for LOI ' + str(int(i)))
        setzero = 1
    else:
        tesloi = tesreqts[tesreqts['COMID'] == comid]
        if len(tesloi) > 0:
            dailyreqts[str(int(i))] = np.nan
            for m in month: #loop through months
                mname = dt.datetime(2019,m,1).strftime('%b').upper()
                # extract Tessmann requirement. May have to adjust provided spreadsheet so it's just first three letters
                # of month name
                mreqt = tesloi[mname + '_Q_TESSMANN'].get_values()[0]
                dailyreqts.loc[dailyreqts.index.month == m,str(int(i))] = mreqt
        else: #couldn't find COMID
            print('COMID = ' +str(int(comid)) + '/LOI ' + str(int(i)) + ' found no values in Tessmann Sheet')
            setzero = 1

    if setzero == 1: #set all IFTs to 0 since Tessmann couldn't be found.
        print('   Setting LOI ' +str(int(i))+ ' to zeros')
        dailyreqts[str(int(i))] = 0

dailyreqts = add_ts_col(dailyreqts)
dailyreqts.to_csv(startdir + 'All LOI Tessmann Flow Requirements.csv')



