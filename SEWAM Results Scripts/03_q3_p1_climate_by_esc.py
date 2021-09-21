#The purpose of this script is to answer question 3 by plotting performance across month/WMT for
# all human scenarios in each ecological scenario:
#•	3. How do climate conditions affect ecological and
# human demand performance at different locations? Alternatively,
# how do ecological and human demand performance vary with
# climate conditions?
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
import seaborn as sns
from plot_performance import plot_df_climate, plot_prf_table

pltloc = './SEWAM Results Analyses/' + \
         'Question 3/Part 1 - By ESC/' #initial location to save plots
# location to save plots annotated with climate and scenario variability
q4loc = './SEWAM Results Analyses/Question 4/'
noepp = [] # list of locations that do not have EPP scenarios
wr, loitab = read_weap_results(recalc=0) #read in daily performance (takes a few minutes, big file)
lois = wr['LOI'].unique().astype(int) # get list of LOIs
#read RSP table
rsptab = pd.read_csv('./Reference Files/Master RSP List.csv',index_col=0)
#sort LOIs by CA
lois = rsptab.loc[np.isin(rsptab['LOI'],lois),:].sort_values(by='Contributing Area')['LOI'].get_values().astype(int)
escs = np.setdiff1d(np.sort(wr['ESC'].unique()), [1])  # remove no IFT eco scenario (esc =1)
sscs = np.setdiff1d(np.sort(wr['SSC'].unique()), [11])  #remove human scenario with no deamnds (ssc = 11)

#initialize dataframes of CMRS values
mntcvseco = pd.DataFrame(index=escs, columns=lois) #ecological frequency reliability against month CMRS
mntcvshlc = pd.DataFrame(index=escs, columns=lois) #local human frequency reliability against month CMRS
mntcvshal = pd.DataFrame(index=escs, columns=lois) #all CA human frequency reliability against month CMRS
wmtcvseco = pd.DataFrame(index=escs, columns=lois) #ecological frequency reliability against WMT CMRS
wmtcvshlc = pd.DataFrame(index=escs, columns=lois) #local human frequency reliability against WMT CMRS
wmtcvshal = pd.DataFrame(index=escs, columns=lois) #all CA human frequency reliability against WMT CMRS

for l in lois: #loop through LOIs
    #status update
    lnum = str(np.where(lois == l)[0][0] + 1)
    print('Processing LOI ' + str(int(l)) + ', ' + str(lnum) + '/' + str(len(lois)))
    loiday = wr.loc[wr['LOI']==l,:] #filter daily performance by LOI
    if l in noepp: #remove EPP scenarios for LOIs listed that don't have them (noepp)
        lescs = escs[escs > 7]
    else:
        lescs = escs

    for esc in lescs: #loop through eco scenarios for this LOI
        elab = get_scn_name(esc=[esc])[0] #get ecological scenario name
        if len(sscs) > 0: #if there are human scenario associated with that eco scenario, make plots
            # make table for eco performance by month and human scenario
            mntplteco = pd.DataFrame(index=np.sort(loiday['month'].unique()))
            # make table for local human performance by month and human scenario
            mntplthlc = pd.DataFrame(index=np.sort(loiday['month'].unique()))
            # make table for all CA human performance by month and human scenario
            mntplthal = pd.DataFrame(index=np.sort(loiday['month'].unique()))

            # make table for eco performance by WMT and human scenario
            wmtplteco = pd.DataFrame(index=np.sort(loiday['WMT'].unique()))
            # make table for local human performance by WMT and human scenario
            wmtplthlc = pd.DataFrame(index=np.sort(loiday['WMT'].unique()))
            # make table for all CA human performance by WMT and human scenario
            wmtplthal = pd.DataFrame(index=np.sort(loiday['WMT'].unique()))

            for ssc in sscs: #loop through human scenarios
                slab = get_scn_name(ssc=[ssc])[0] #get string of human scenario name
                scnday = loiday.loc[(loiday['ESC'] == esc) & (loiday['SSC'] == ssc)] #filter daily performance by eco and human scenario

                # get total number of days in each month
                mnttot = scnday.groupby('month').count()['Eco Met']
                # get number of days IFT met in each month
                mntmeteco = scnday.groupby('month').sum()['Eco Met']
                # calculate eco frequency reliabilty
                mntplteco.loc[:, ssc] = mntmeteco.loc[mntplteco.index] / mnttot.loc[mntplteco.index]
                # get number of days local human demands met in each month
                mntmethlc = scnday.groupby('month').sum()['Hum Local Met']
                # calculate local human demand frequency reliabilty
                mntplthlc.loc[:, ssc] = mntmethlc.loc[mntplthlc.index] / mnttot.loc[mntplthlc.index]
                # get number of days all CA human demands met in each month
                mntmethal = scnday.groupby('month').sum()['Hum All Met']
                # calculate all CA human demand frequency reliabilty
                mntplthal.loc[:,ssc] = mntmethal.loc[mntplthal.index]/mnttot.loc[mntplthal.index]

                # get total number of days in each WMT
                wmttot = scnday.groupby('WMT').count()['Eco Met']
                # get number of days IFT met in each WMT
                wmtmeteco = scnday.groupby('WMT').sum()['Eco Met']
                # calculate eco frequency reliabilty
                wmtplteco.loc[:, ssc] = wmtmeteco.loc[wmtplteco.index] / wmttot.loc[wmtplteco.index]
                # get number of days local human demands met in each WMT
                wmtmethlc = scnday.groupby('WMT').sum()['Hum Local Met']
                # calculate local human demand frequency reliabilty
                wmtplthlc.loc[:, ssc] = wmtmethlc.loc[wmtplthlc.index] / wmttot.loc[wmtplthlc.index]
                # get number of days all CA human demands met in each WMT
                wmtmethal = scnday.groupby('WMT').sum()['Hum All Met']
                # calculate all CA human demand frequency reliabilty
                wmtplthal.loc[:, ssc] = wmtmethal.loc[wmtplthal.index] / wmttot.loc[wmtplthal.index]


            #Plot monthly performance and return CMRS value to be stored in the table
            mntcvseco.loc[esc, l] = plot_df_climate(mntplteco, mw=1, elatype=1, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)
            mntcvshlc.loc[esc, l] = plot_df_climate(mntplthlc, mw=1, elatype=2, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)
            mntcvshal.loc[esc, l] = plot_df_climate(mntplthal, mw=1, elatype=3, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)

            #plot performance by WMT and return CMRS value to be stored in table
            wmtcvseco.loc[esc, l] = plot_df_climate(wmtplteco, mw=2, elatype=1, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)
            wmtcvshlc.loc[esc, l] = plot_df_climate(wmtplthlc, mw=2, elatype=2, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)
            wmtcvshal.loc[esc, l] = plot_df_climate(wmtplthal, mw=2, elatype=3, l=l, scnum=esc, pltloc=pltloc, q4loc=q4loc, se=0)


# plot CMRS tables by LOI
esclab = get_scn_name(esc=mntcvseco.index) # get ecological scenario names
bsvstr = 'All LOIs Climate vs SSC Variability' #string for plot label
plot_prf_table(mntcvseco,mw=1,elatype=1,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)
plot_prf_table(mntcvshlc,mw=1,elatype=2,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)
plot_prf_table(mntcvshal,mw=1,elatype=3,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)

plot_prf_table(wmtcvseco,mw=2,elatype=1,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)
plot_prf_table(wmtcvshlc,mw=2,elatype=2,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)
plot_prf_table(wmtcvshal,mw=2,elatype=3,pltloc=q4loc,bstr=bsvstr,xtls=lois,ytls=esclab, se=1)
