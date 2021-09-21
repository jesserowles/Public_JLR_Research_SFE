import sys
sys.path.insert(1, './IFT Calculation Scripts')
import calendar
import datetime as dt
import numpy as np
import pandas as pd
import os
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from statsmodels.nonparametric.smoothers_lowess import lowess as lw
from loess.loess_1d import loess_1d as ls
from add_ts_col import add_ts_col

from get_all_sfe_lois import get_all_sfe_lois

startdir = 'IFT Results/'
# rwoodlois, loi = get_redwood_loi_table()
loitab, loi, fultab = get_all_sfe_lois()
avgwin = 30 #window size of moving average
switchdays = 30 # number of days to look from beginning and end of list of dates to determine when to switch between LOESS and moving average
startdate = dt.datetime(1995,10,1)
stopdate = dt.datetime(2017,9,30)
alldates = pd.date_range(startdate,stopdate)


# The following variables can have a single value or a list of values (i.e., [#1, #2, #3,...]). The script loops through
# however many values are put in
exd_perc_flows = [0.1] #[0.1, 0.2, 0.3] #the exceedance percentile flow to create the streamflow baseline (default = 10% or 0.1)
divert_ratios = [0.1] #[0.1, 0.2, 0.3] #proportion of streamflow baseline for setting diversion allocation (default = 10% or 0.1)
prd_pct_reqts = [0.9] #percentile of the length of time the requirement applies, as specified in reqt_time. For example,
# if this is 0.1, the 10th percentile of all flows
reqt_times = [0] #[0,1,2,3] #length of time for requirements to apply. 0 for daily, 1 for weekly, 2 for semi-monthly (1st and 15th), 3 for monthly

print(dt.datetime.now().strftime('%b-%d-%Y %I:%M:%S %p'))
#loop through all selections
for e in exd_perc_flows:
    for d in divert_ratios:
        for r in reqt_times:
            for p in prd_pct_reqts:
                mpofout = pd.DataFrame(columns=loi, index=alldates)
                if (not r == 0) or ((r == 0) and (p == prd_pct_reqts[len(prd_pct_reqts)-1])): #don't do daily for every different p
                    #determine MPOF variation labels
                    exdstr = str(int(e * 100)) + 'th Percentile Hydrograph, '
                    pctstr = str(int(d * 100)) + '%'
                    prdstr = str(int(p * 100)) + 'th Percentile of '
                    if r == 0:
                        lenstr = 'Daily'
                        prdstr = ''
                    elif r == 1:
                        lenstr = 'Weekly'
                    elif r == 2:
                        lenstr = 'Biweekly' #Note: not perfectly biweekly, but new requirements set on the 1st and 15th of each month
                    elif r == 3:
                        lenstr = 'Monthly'
                    methstr = pctstr+ ' of ' +exdstr+ prdstr+lenstr
                    if (e == 0.1) & (d == 0.1) & (r == 0):
                        methstr = 'Default'
                    methstr = 'MPOF - ' + methstr
                    for l in loi:
                        unimp = read_loi_paradigm_flow(l) #read in unimpaired flow

                        # determine exceedance hydrograph from unimpaired flow
                        flow90exd = unimp['flow'].groupby(by=[unimp.index.month, unimp.index.day]).quantile(e)
                        #fix for water year order of months
                        prevyr = flow90exd.loc[np.arange(10,13)]
                        flow90exd = prevyr.append(flow90exd.loc[np.arange(1, 10)])

                        tempind = [dt.datetime(1995,10,1)+dt.timedelta(x) for x in range(366)]
                        flow90exd.index = tempind
                        loessind = flow90exd.index
                        loessfilt = lw(flow90exd.get_values(), loessind, frac=70 / 365, it=0) #70-day loess filter

                        # moving average
                        flowmovavg= flow90exd.append(flow90exd)
                        mastr = str(avgwin) + '-Day MA'
                        movavg_dups = flowmovavg.rolling(avgwin,center=True).mean().dropna().sort_index() #calculate rolling/moving avg
                        movavg = movavg_dups.loc[~movavg_dups.index.duplicated(keep='first')] #remove duplicates
                        #format into table
                        flowbase = pd.DataFrame({'Daily 90% Exceedance': flow90exd, mastr: movavg, 'LOESS': loessfilt[:,1]},index=flow90exd.index)
                        methdiff = np.abs(flowbase[mastr]-flowbase['LOESS']) #difference between moving avg and loess
                        #determine day within beginning and ending number of days to swtich from loess to moving avg (default = 30)
                        headswitch = methdiff.index[1:switchdays+1][methdiff.iloc[1:switchdays+1] == min(methdiff.iloc[1:switchdays+1])]
                        tailswitch = methdiff.index[-(switchdays+1):-1][methdiff.iloc[-(switchdays+1):-1] == min(methdiff.iloc[-(switchdays+1):-1])]
                        #determine streamflow baseline from combination of methods
                        flowbase['Daily Streamflow Baseline (cfs)'] = flowbase.loc[min(flowbase.index):pd.DatetimeIndex(headswitch-pd.DateOffset(1)).to_pydatetime()[0],mastr].append(
                            flowbase.loc[headswitch.to_pydatetime()[0]:(tailswitch-pd.DateOffset(1)).to_pydatetime()[0],'LOESS']).append(
                            flowbase.loc[tailswitch.to_pydatetime()[0]:max(flowbase.index),mastr])


                        if r == 0: #daily, no resampling needed
                            reindfb = flowbase.copy()
                        else:
                            if r == 1: # weekly
                                freqdates = [min(flowbase.index) + (dt.timedelta(days=7) * i) for i in range(0, 53)]
                                gbinds = np.zeros_like(flowbase.index,dtype='int')
                                for i in range(0, len(freqdates)):
                                    gbinds[(flowbase.index < freqdates[i]) & (gbinds == 0)] = i
                                gbinds[gbinds == 0] = 53
                                indfq = 'W'
                            elif r == 2: #biweekly
                                days = np.array([1,15])
                                months = np.append(np.arange(10,13),np.arange(1, 10))
                                years = np.append(1995 * np.ones(6), 1996 * np.ones(18)).astype(int)
                                dates = np.array(np.meshgrid(months, days)).T.reshape(-1, 2)
                                freqdates = [dt.datetime(years[i],dates[i,0], dates[i,1]) for i in range(len(dates))]
                                gbinds = np.zeros_like(flowbase.index,dtype='int')
                                for i in range(0, len(freqdates)):
                                    gbinds[(flowbase.index < freqdates[i]) & (gbinds == 0)] = i
                                gbinds[gbinds == 0] = 24
                                indfq = 'SMS'
                            elif r == 3: #monthly
                                gbinds = flowbase.index.month
                                indfq = 'MS'
                            reindfb = flowbase.groupby(gbinds, sort=False).quantile(p) #group by time period and take quantile
                            reindfb.index = pd.date_range(min(tempind), max(tempind), freq=indfq)
                            reindfb = reindfb.reindex(flowbase.index, method='ffill')
                        #calculate diverion allocation, both daily and resampled (may be the same if both are daily)
                        flowbase['Daily Diversion Allocation (cfs)'] = d * flowbase['Daily Streamflow Baseline (cfs)']
                        flowbase['Resampled Streamflow Baseline (cfs)'] = reindfb['Daily Streamflow Baseline (cfs)']
                        flowbase['Resampled Diversion Allocation (cfs)'] = d * reindfb['Daily Streamflow Baseline (cfs)']

                        #save off calculations performed so results can be analyzed manually
                        if not(os.path.exists(startdir + '/' + methstr)):
                            os.mkdir(startdir + '/' + methstr)
                        flowbase.to_excel(startdir + methstr + '/LOI ' + l + ' MPOF ' + methstr + ' Data.xlsx')

                        #now need to take calculated diversion allocation and subtract it  from unimpaired flow to get IFT
                        fbst = flowbase.copy()
                        fbst.index = flowbase.index.strftime('%m-%d')
                        years = np.arange(min(alldates.year), max(alldates.year)+1)
                        #need to copy diversion allocation to all years
                        fballyr = pd.concat([fbst]*(years[-1]-years[0]))
                        alyind = (np.concatenate([np.repeat(years[0],92), \
                                                  np.repeat(years[1:-1],366), \
                                                  np.repeat(years[-1],274)]) \
                                  .astype(str)+fballyr.index)
                        fballyr.index = alyind
                        for y in years[1:]:
                            if ~calendar.isleap(y):
                                fballyr.drop(index=str(y)+'02-29',inplace=True) #remove feb 29 where it doesn't exist
                        fballyr.index = pd.to_datetime(fballyr.index,format='%Y%m-%d')
                        mpofout.loc[mpofout.index,l] = unimp.loc[mpofout.index,'flow'] - fballyr.loc[mpofout.index,'Resampled Diversion Allocation (cfs)']

                        mpofout.loc[mpofout[l] < 0, l] = 0 #can't have negative IFT
                    #format for WEAP and save
                    mpofout = add_ts_col(mpofout)
                    savdir = startdir
                    if not ((e == 0.1) & (d == 0.1) & (r == 0)):
                        savdir = startdir + 'MPOF Variants/'
                    mpofout.to_csv(savdir + 'All LOI ' +methstr+ ' IFTs.csv')
                    print(methstr + ' Complete')

print(dt.datetime.now().strftime('%b-%d-%Y %I:%M:%S %p'))