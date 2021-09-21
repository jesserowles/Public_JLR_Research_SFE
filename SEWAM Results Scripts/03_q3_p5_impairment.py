# The purpose of this script is to answer question 3 for impairment and standardized impairment:
# •	3. How do climate conditions affect ecological and
# human demand performance at different locations? Alternatively,
# how do ecological and human demand performance vary with
# climate conditions?
# For variables:
#   _dev means mean impairment
#   _dpf means mean standardized impairment
#   _3dv means max 3-day MA impairment
#   _3pf means max 3-day MA standardized impairment
#   _5dv means max 5-day MA impairment
#   _5pf means max 5-day MA standardized impairment
#   _7dv means max 7-day MA impairment
#   _7pf means max 7-day MA standardized impairment

import sys
sys.path.insert(1,'./SEWAM Results Scripts')
from lookup_scenarios import get_scn_name
from weap_results_v2 import read_weap_results
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import scipy.stats as stats
import calendar as cal
from mpl_toolkits.mplot3d import Axes3D as a3d
from matplotlib import cm
from plot_performance import plot_def, plot_prf_table


pltloc = './SEWAM Results Analyses/' + \
         'Question 3/Part 5 - Deficit From Unimpaired/' #original location to save plots

#annotated plot folder
q4loc = './SEWAM Results Analyses/Question 4/'

wr, loitab = read_weap_results(recalc=0) #read in daily performance
lois = wr['LOI'].unique() #list of LOIs
noepp = [2230, 2210, 2110, 2120, 2095] #list of LOIs that don't have EPP
escs = np.setdiff1d(np.sort(wr['ESC'].unique()),
                        [1])  #get list of all eco scenarios without no IFT (esc=1)
sscs = np.setdiff1d(np.sort(wr['SSC'].unique()), [11])  # get all human scenarios except 11 (no demands)
#read in RSP table
rsptab = pd.read_csv('./Reference Files/Master RSP List.csv',index_col=0)
lois = rsptab.loc[np.isin(rsptab['LOI'],lois),:].sort_values(by='Contributing Area')['LOI'].get_values() #sort LOI by CA

# intialize month across eco scenario
mntcvsdevesc = pd.DataFrame(index=escs, columns=lois)
mntcvsdpfesc = pd.DataFrame(index=escs, columns=lois)
mntcvs3dvesc = pd.DataFrame(index=escs, columns=lois)
mntcvs3pfesc = pd.DataFrame(index=escs, columns=lois)
mntcvs5dvesc = pd.DataFrame(index=escs, columns=lois)
mntcvs5pfesc = pd.DataFrame(index=escs, columns=lois)
mntcvs7dvesc = pd.DataFrame(index=escs, columns=lois)
mntcvs7pfesc = pd.DataFrame(index=escs, columns=lois)

# intialize WMT across eco scenario
wmtcvsdevesc = pd.DataFrame(index=escs, columns=lois)
wmtcvsdpfesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs3dvesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs3pfesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs5dvesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs5pfesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs7dvesc = pd.DataFrame(index=escs, columns=lois)
wmtcvs7pfesc = pd.DataFrame(index=escs, columns=lois)

# intialize month across human scenario
mntcvsdevssc = pd.DataFrame(index=sscs, columns=lois)
mntcvsdpfssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs3dvssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs3pfssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs5dvssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs5pfssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs7dvssc = pd.DataFrame(index=sscs, columns=lois)
mntcvs7pfssc = pd.DataFrame(index=sscs, columns=lois)

# intialize WMT across human scenario
wmtcvsdevssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvsdpfssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs3dvssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs3pfssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs5dvssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs5pfssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs7dvssc = pd.DataFrame(index=sscs, columns=lois)
wmtcvs7pfssc = pd.DataFrame(index=sscs, columns=lois)

for l in lois: #loop through LOIs
    #status update
    lnum = str(np.where(lois == l)[0][0] + 1)
    print('Processing LOI ' + str(int(l)) + ', ' + str(lnum) + '/' + str(len(lois)))
    loiday = wr.loc[wr['LOI'] == l, :] #filter daily performance table by LOI
    unimp = loiday.loc[(loiday['ESC'] == 1) & (loiday['SSC'] == 11),:] #use no demands, no IFT scenario for LOI as unimpaired
    mntunflw = unimp.groupby('month').mean()['flow'] #mean monthly flow
    wmtunflw = unimp.groupby('WMT').mean()['flow'] #mean WMT flow
    if l in noepp: #remove EPP scenarios in locations without them
        lescs = escs[escs > 7]
    else:
        lescs = escs

    #create impairment plots for each eco scenario against human scenarios
    for esc in lescs: # loop through eco scenarios
        elab = get_scn_name(esc=[esc])[0] #label for ecological scenario
        if len(sscs) > 0: #if human scenarios exist in the eco scenario, process and plot them
            #month performance tables against human scenarios
            mntpltdev = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntpltdpf = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt3dv = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt3pf = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt5dv = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt5pf = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt7dv = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)
            mntplt7pf = pd.DataFrame(index=np.sort(loiday['month'].unique()),columns=sscs)

            # WMT performance tables against human scenarios
            wmtpltdev = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtpltdpf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt3dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt3pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt5dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt5pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt7dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)
            wmtplt7pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()),columns=sscs)

            for ssc in sscs: #loop thru human scenarios
                slab = get_scn_name(ssc=[ssc])[0] #human sceanrio label
                scnday = loiday.loc[(loiday['ESC'] == esc) & (loiday['SSC'] == ssc)] #filter daily performance by scenario

                # for month,
                mntpltdev.loc[:,ssc] = scnday.groupby('month').mean()['Impairment'] #calculate mean imp
                mntpltdpf.loc[:,ssc] = scnday.groupby('month').mean()['Standardized Impairment'] #calculate mean stnd imp
                mntplt3dv.loc[:,ssc] = scnday.groupby('month').max()['3 Day Moving Avg Impairment'] #determine max 3-day MA imp
                mntplt3pf.loc[:,ssc] = scnday.groupby('month').max()['3 Day Moving Avg Standardized Impairment'] #determine max 3-day MA stnd imp
                mntplt5dv.loc[:,ssc] = scnday.groupby('month').max()['5 Day Moving Avg Impairment'] #determine max 5-day MA imp
                mntplt5pf.loc[:,ssc] = scnday.groupby('month').max()['5 Day Moving Avg Standardized Impairment'] #determine max 5-day MA stnd imp
                mntplt7dv.loc[:,ssc] = scnday.groupby('month').max()['7 Day Moving Avg Impairment'] #determine max 7-day MA imp
                mntplt7pf.loc[:,ssc] = scnday.groupby('month').max()['7 Day Moving Avg Standardized Impairment'] #determine max 7-day MA stnd imp

                #do the same for WMT
                wmtpltdev.loc[:,ssc] = scnday.groupby('WMT').mean()['Impairment']
                wmtpltdpf.loc[:,ssc] = scnday.groupby('WMT').mean()['Standardized Impairment']
                wmtplt3dv.loc[:,ssc] = scnday.groupby('WMT').max()['3 Day Moving Avg Impairment']
                wmtplt3pf.loc[:,ssc] = scnday.groupby('WMT').max()['3 Day Moving Avg Standardized Impairment']
                wmtplt5dv.loc[:,ssc] = scnday.groupby('WMT').max()['5 Day Moving Avg Impairment']
                wmtplt5pf.loc[:,ssc] = scnday.groupby('WMT').max()['5 Day Moving Avg Standardized Impairment']
                wmtplt7dv.loc[:,ssc] = scnday.groupby('WMT').max()['7 Day Moving Avg Impairment']
                wmtplt7pf.loc[:,ssc] = scnday.groupby('WMT').max()['7 Day Moving Avg Standardized Impairment']

            #plotting functions with CMRS values returned
            #month
            mntcvsdevesc.loc[esc,l] = plot_def(mntpltdev, 1, 1, l, 1, elab, pltloc, q4loc)
            mntcvsdpfesc.loc[esc,l] = plot_def(mntpltdpf, 1, 2, l, 1, elab, pltloc, q4loc)
            mntcvs3dvesc.loc[esc,l] = plot_def(mntplt3dv, 1, 1, l, 1, elab, pltloc, q4loc, defma=3)
            mntcvs3pfesc.loc[esc,l] = plot_def(mntplt3pf, 1, 2, l, 1, elab, pltloc, q4loc, defma=3)
            mntcvs5dvesc.loc[esc,l] = plot_def(mntplt5dv, 1, 1, l, 1, elab, pltloc, q4loc, defma=5)
            mntcvs5pfesc.loc[esc,l] = plot_def(mntplt5pf, 1, 2, l, 1, elab, pltloc, q4loc, defma=5)
            mntcvs7dvesc.loc[esc,l] = plot_def(mntplt7dv, 1, 1, l, 1, elab, pltloc, q4loc, defma=7)
            mntcvs7pfesc.loc[esc,l] = plot_def(mntplt7pf, 1, 2, l, 1, elab, pltloc, q4loc, defma=7)

            #WMT
            wmtcvsdevesc.loc[esc,l] = plot_def(wmtpltdev, 2, 1, l, 1, elab, pltloc, q4loc)
            wmtcvsdpfesc.loc[esc,l] = plot_def(wmtpltdpf, 2, 2, l, 1, elab, pltloc, q4loc)
            wmtcvs3dvesc.loc[esc,l] = plot_def(wmtplt3dv, 2, 1, l, 1, elab, pltloc, q4loc, defma=3)
            wmtcvs3pfesc.loc[esc,l] = plot_def(wmtplt3pf, 2, 2, l, 1, elab, pltloc, q4loc, defma=3)
            wmtcvs5dvesc.loc[esc,l] = plot_def(wmtplt5dv, 2, 1, l, 1, elab, pltloc, q4loc, defma=5)
            wmtcvs5pfesc.loc[esc,l] = plot_def(wmtplt5pf, 2, 2, l, 1, elab, pltloc, q4loc, defma=5)
            wmtcvs7dvesc.loc[esc,l] = plot_def(wmtplt7dv, 2, 1, l, 1, elab, pltloc, q4loc, defma=7)
            wmtcvs7pfesc.loc[esc,l] = plot_def(wmtplt7pf, 2, 2, l, 1, elab, pltloc, q4loc, defma=7)

    #now make plots for each human scenario in all eco scenarios
    for ssc in sscs: #loop thru human scenarios
        slab = get_scn_name(ssc=[ssc])[0] #get human scen label
        escs = np.setdiff1d(np.sort(loiday['ESC'].unique()),
                            [1])  #remove eco scenario = 1, no IFT
        if l in noepp: #for locations with no EPPs, remove those
            lescs = escs[escs > 7]
        else:
            lescs = escs

        if len(sscs) > 0:
            mntpltdev = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntpltdpf = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt3dv = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt3pf = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt5dv = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt5pf = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt7dv = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)
            mntplt7pf = pd.DataFrame(index=np.sort(loiday['month'].unique()), columns=lescs)

            wmtpltdev = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtpltdpf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt3dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt3pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt5dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt5pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt7dv = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)
            wmtplt7pf = pd.DataFrame(index=np.sort(loiday['WMT'].unique()), columns=lescs)

            for esc in lescs: #loop through eco scenarios
                elab = get_scn_name(esc=[esc])[0] #eco scenario label
                scnday = loiday.loc[(loiday['ESC'] == esc) & (loiday['SSC'] == ssc)] #filter dialy performance by scenario

                # do same as previous section calculations for month
                mntpltdev.loc[:, esc] = scnday.groupby('month').mean()['Impairment']
                mntpltdpf.loc[:, esc] = scnday.groupby('month').mean()['Standardized Impairment']
                mntplt3dv.loc[:, esc] = scnday.groupby('month').max()['3 Day Moving Avg Impairment']
                mntplt3pf.loc[:, esc] = scnday.groupby('month').max()['3 Day Moving Avg Standardized Impairment']
                mntplt5dv.loc[:, esc] = scnday.groupby('month').max()['5 Day Moving Avg Impairment']
                mntplt5pf.loc[:, esc] = scnday.groupby('month').max()['5 Day Moving Avg Standardized Impairment']
                mntplt7dv.loc[:, esc] = scnday.groupby('month').max()['7 Day Moving Avg Impairment']
                mntplt7pf.loc[:, esc] = scnday.groupby('month').max()['7 Day Moving Avg Standardized Impairment']

                #and WMT
                wmtpltdev.loc[:, esc] = scnday.groupby('WMT').mean()['Impairment']
                wmtpltdpf.loc[:, esc] = scnday.groupby('WMT').mean()['Standardized Impairment']
                wmtplt3dv.loc[:, esc] = scnday.groupby('WMT').max()['3 Day Moving Avg Impairment']
                wmtplt3pf.loc[:, esc] = scnday.groupby('WMT').max()['3 Day Moving Avg Standardized Impairment']
                wmtplt5dv.loc[:, esc] = scnday.groupby('WMT').max()['5 Day Moving Avg Impairment']
                wmtplt5pf.loc[:, esc] = scnday.groupby('WMT').max()['5 Day Moving Avg Standardized Impairment']
                wmtplt7dv.loc[:, esc] = scnday.groupby('WMT').max()['7 Day Moving Avg Impairment']
                wmtplt7pf.loc[:, esc] = scnday.groupby('WMT').max()['7 Day Moving Avg Standardized Impairment']

            #plotting functions that return CMRS values for month
            mntcvsdevssc.loc[ssc,l] = plot_def(mntpltdev, 1, 1, l, 2, slab, pltloc, q4loc)
            mntcvsdpfssc.loc[ssc,l] = plot_def(mntpltdpf, 1, 2, l, 2, slab, pltloc, q4loc)
            mntcvs3dvssc.loc[ssc,l] = plot_def(mntplt3dv, 1, 1, l, 2, slab, pltloc, q4loc, defma=3)
            mntcvs3pfssc.loc[ssc,l] = plot_def(mntplt3pf, 1, 2, l, 2, slab, pltloc, q4loc, defma=3)
            mntcvs5dvssc.loc[ssc,l] = plot_def(mntplt5dv, 1, 1, l, 2, slab, pltloc, q4loc, defma=5)
            mntcvs5pfssc.loc[ssc,l] = plot_def(mntplt5pf, 1, 2, l, 2, slab, pltloc, q4loc, defma=5)
            mntcvs7dvssc.loc[ssc,l] = plot_def(mntplt7dv, 1, 1, l, 2, slab, pltloc, q4loc, defma=7)
            mntcvs7pfssc.loc[ssc,l] = plot_def(mntplt7pf, 1, 2, l, 2, slab, pltloc, q4loc, defma=7)

            # plotting functions that return CMRS values for WMT
            wmtcvsdevssc.loc[ssc,l] = plot_def(wmtpltdev, 2, 1, l, 2, slab, pltloc, q4loc)
            wmtcvsdpfssc.loc[ssc,l] = plot_def(wmtpltdpf, 2, 2, l, 2, slab, pltloc, q4loc)
            wmtcvs3dvssc.loc[ssc,l] = plot_def(wmtplt3dv, 2, 1, l, 2, slab, pltloc, q4loc, defma=3)
            wmtcvs3pfssc.loc[ssc,l] = plot_def(wmtplt3pf, 2, 2, l, 2, slab, pltloc, q4loc, defma=3)
            wmtcvs5dvssc.loc[ssc,l] = plot_def(wmtplt5dv, 2, 1, l, 2, slab, pltloc, q4loc, defma=5)
            wmtcvs5pfssc.loc[ssc,l] = plot_def(wmtplt5pf, 2, 2, l, 2, slab, pltloc, q4loc, defma=5)
            wmtcvs7dvssc.loc[ssc,l] = plot_def(wmtplt7dv, 2, 1, l, 2, slab, pltloc, q4loc, defma=7)
            wmtcvs7pfssc.loc[ssc,l] = plot_def(wmtplt7pf, 2, 2, l, 2, slab, pltloc, q4loc, defma=7)

#plot CMRS heat maps
print('Finished individual locations, plotting climate vs sensitivity tables')
ssclab = get_scn_name(ssc=sscs) #human scenario labels
bsvstr = 'All LOIs Climate vs ESC Variability' #string for plot label
lints = lois.astype(int) #format LOIs as int to remove decimal
#by month
plot_prf_table(mntcvsdevssc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0)
plot_prf_table(mntcvsdpfssc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0)
plot_prf_table(mntcvs3dvssc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 3)
plot_prf_table(mntcvs3pfssc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 3)
plot_prf_table(mntcvs5dvssc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 5)
plot_prf_table(mntcvs5pfssc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 5)
plot_prf_table(mntcvs7dvssc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 7)
plot_prf_table(mntcvs7pfssc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 7)

#by WMT
plot_prf_table(wmtcvsdevssc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0)
plot_prf_table(wmtcvsdpfssc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0)
plot_prf_table(wmtcvs3dvssc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 3)
plot_prf_table(wmtcvs3pfssc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 3)
plot_prf_table(wmtcvs5dvssc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 5)
plot_prf_table(wmtcvs5pfssc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 5)
plot_prf_table(wmtcvs7dvssc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 7)
plot_prf_table(wmtcvs7pfssc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=ssclab, se = 0, defma = 7)

esclab = get_scn_name(esc=escs) #eco scenario labels
bsvstr = 'All LOIs Climate vs SSC Variability' #plot label
#by month
plot_prf_table(mntcvsdevesc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1)
plot_prf_table(mntcvsdpfesc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1)
plot_prf_table(mntcvs3dvesc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 3)
plot_prf_table(mntcvs3pfesc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 3)
plot_prf_table(mntcvs5dvesc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 5)
plot_prf_table(mntcvs5pfesc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 5)
plot_prf_table(mntcvs7dvesc,mw=1,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 7)
plot_prf_table(mntcvs7pfesc,mw=1,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 7)

#by WMT
plot_prf_table(wmtcvsdevesc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1)
plot_prf_table(wmtcvsdpfesc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1)
plot_prf_table(wmtcvs3dvesc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 3)
plot_prf_table(wmtcvs3pfesc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 3)
plot_prf_table(wmtcvs5dvesc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 5)
plot_prf_table(wmtcvs5pfesc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 5)
plot_prf_table(wmtcvs7dvesc,mw=2,elatype=4,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 7)
plot_prf_table(wmtcvs7pfesc,mw=2,elatype=5,pltloc=q4loc,bstr=bsvstr,xtls=lints,ytls=esclab, se = 1, defma = 7)