#The purpose of this script is to answer question 3 by creating performance tables
# 1. for all scenario combinations at a single location in a single month, WMT, or over the entire POR
# 2. the max difference across one scenario type against location
# 3. mean performance across one scenario type against location
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
from plot_performance import process_and_plot_table, plot_md_mn_table

#plot location
pltloc = './SEWAM Results Analyses/Question 3/Part 3 - By Month & WMT/'


wr, loitab = read_weap_results(recalc=0, ltonly = 0) #read in daily data
lois = wr['LOI'].unique() #list of LOIs
mnum = np.sort(wr['month'].unique()) #get list of months
wmtnum = np.sort(wr['WMT'].unique()) #get list of WMTs

noepp = [] #locations with no EPP scenarios

forind = wr.loc[~(wr['ESC']==1) & ~(wr['SSC']==11),:] #remove No IFT (esc=  1) and no demand (ssc = 11) scenarios

#initialize Max difference tables
# by month across eco scenarios
mntescind = forind.groupby(['month','ESC']).count().index #get index for month and eco scenarios
mntmdesceco = pd.DataFrame(index=mntescind, columns=lois) #eco frequency reliability
mntmdeschlc = pd.DataFrame(index=mntescind, columns=lois) #local human frequency reliability
mntmdeschal = pd.DataFrame(index=mntescind, columns=lois) #all CA human frequency reliability
mntmdescdef = pd.DataFrame(index=mntescind, columns=lois) #impairment
mntmdescprp = pd.DataFrame(index=mntescind, columns=lois) #standardized impairment
mntmdesc3df = pd.DataFrame(index=mntescind, columns=lois) #max 3-day MA impairment
mntmdesc3pr = pd.DataFrame(index=mntescind, columns=lois) #max 3-day MA standardized impairment
mntmdesc5df = pd.DataFrame(index=mntescind, columns=lois) #max 5-day MA impairment
mntmdesc5pr = pd.DataFrame(index=mntescind, columns=lois) #max 5-day MA standardized impairment
mntmdesc7df = pd.DataFrame(index=mntescind, columns=lois) #max 7-day MA impairment
mntmdesc7pr = pd.DataFrame(index=mntescind, columns=lois) #max 7-day MA standardized impairment

# by month across human scenarios
mntsscind = forind.groupby(['month','SSC']).count().index
mntmdssceco = pd.DataFrame(index=mntsscind,columns=lois) #eco frequency reliability
mntmdsschlc = pd.DataFrame(index=mntsscind,columns=lois) #local human frequency reliability
mntmdsschal = pd.DataFrame(index=mntsscind,columns=lois) #all CA human frequency reliability
mntmdsscdef = pd.DataFrame(index=mntsscind,columns=lois) #impairment
mntmdsscprp = pd.DataFrame(index=mntsscind,columns=lois) #standardized impairment
mntmdssc3df = pd.DataFrame(index=mntsscind,columns=lois) #max 3-day MA impairment
mntmdssc3pr = pd.DataFrame(index=mntsscind,columns=lois) #max 3-day MA standardized impairment
mntmdssc5df = pd.DataFrame(index=mntsscind,columns=lois) #max 5-day MA impairment
mntmdssc5pr = pd.DataFrame(index=mntsscind,columns=lois) #max 5-day MA standardized impairment
mntmdssc7df = pd.DataFrame(index=mntsscind,columns=lois) #max 7-day MA impairment
mntmdssc7pr = pd.DataFrame(index=mntsscind,columns=lois) #max 7-day MA standardized impairment

# by WMT across eco scenarios
wmtescind = forind.groupby(['WMT','ESC']).count().index
wmtmdesceco = pd.DataFrame(index=wmtescind,columns=lois) #eco frequency reliability
wmtmdeschlc = pd.DataFrame(index=wmtescind,columns=lois) #local human frequency reliability
wmtmdeschal = pd.DataFrame(index=wmtescind,columns=lois) #all CA human frequency reliability
wmtmdescdef = pd.DataFrame(index=wmtescind,columns=lois) #impairment
wmtmdescprp = pd.DataFrame(index=wmtescind,columns=lois) #standardized impairment
wmtmdesc3df = pd.DataFrame(index=wmtescind,columns=lois) #max 3-day MA impairment
wmtmdesc3pr = pd.DataFrame(index=wmtescind,columns=lois) #max 3-day MA standardized impairment
wmtmdesc5df = pd.DataFrame(index=wmtescind,columns=lois) #max 5-day MA impairment
wmtmdesc5pr = pd.DataFrame(index=wmtescind,columns=lois) #max 5-day MA standardized impairment
wmtmdesc7df = pd.DataFrame(index=wmtescind,columns=lois) #max 7-day MA impairment
wmtmdesc7pr = pd.DataFrame(index=wmtescind,columns=lois) #max 7-day MA standardized impairment

# by WMT across human scenarios
wmtsscind = forind.groupby(['WMT','SSC']).count().index
wmtmdssceco = pd.DataFrame(index=wmtsscind,columns=lois) #eco frequency reliability
wmtmdsschlc = pd.DataFrame(index=wmtsscind,columns=lois) #local human frequency reliability
wmtmdsschal = pd.DataFrame(index=wmtsscind,columns=lois) #all CA human frequency reliability
wmtmdsscdef = pd.DataFrame(index=wmtsscind,columns=lois) #impairment
wmtmdsscprp = pd.DataFrame(index=wmtsscind,columns=lois) #standardized impairment
wmtmdssc3df = pd.DataFrame(index=wmtsscind,columns=lois) #max 3-day MA impairment
wmtmdssc3pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 3-day MA standardized impairment
wmtmdssc5df = pd.DataFrame(index=wmtsscind,columns=lois) #max 5-day MA impairment
wmtmdssc5pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 5-day MA standardized impairment
wmtmdssc7df = pd.DataFrame(index=wmtsscind,columns=lois) #max 7-day MA impairment
wmtmdssc7pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 7-day MA standardized impairment

# over entire POR across eco scenarios
allescind = np.sort(forind['ESC'].unique())
allmdesceco = pd.DataFrame(index=allescind, columns=lois) #eco frequency reliability
allmdeschlc = pd.DataFrame(index=allescind, columns=lois) #local human frequency reliability
allmdeschal = pd.DataFrame(index=allescind, columns=lois) #all CA human frequency reliability
allmdescdef = pd.DataFrame(index=allescind, columns=lois) #impairment
allmdescprp = pd.DataFrame(index=allescind, columns=lois) #standardized impairment
allmdesc3df = pd.DataFrame(index=allescind, columns=lois) #max 3-day MA impairment
allmdesc3pr = pd.DataFrame(index=allescind, columns=lois) #max 3-day MA standardized impairment
allmdesc5df = pd.DataFrame(index=allescind, columns=lois) #max 5-day MA impairment
allmdesc5pr = pd.DataFrame(index=allescind, columns=lois) #max 5-day MA standardized impairment
allmdesc7df = pd.DataFrame(index=allescind, columns=lois) #max 7-day MA impairment
allmdesc7pr = pd.DataFrame(index=allescind, columns=lois) #max 7-day MA standardized impairment

# over entire POR across human scenarios
allsscind = np.sort(forind['SSC'].unique())
allmdssceco = pd.DataFrame(index=allsscind,columns=lois) #eco frequency reliability
allmdsschlc = pd.DataFrame(index=allsscind,columns=lois) #local human frequency reliability
allmdsschal = pd.DataFrame(index=allsscind,columns=lois) #all CA human frequency reliability
allmdsscdef = pd.DataFrame(index=allsscind,columns=lois) #impairment
allmdsscprp = pd.DataFrame(index=allsscind,columns=lois) #standardized impairment
allmdssc3df = pd.DataFrame(index=allsscind,columns=lois) #max 3-day MA impairment
allmdssc3pr = pd.DataFrame(index=allsscind,columns=lois) #max 3-day MA standardized impairment
allmdssc5df = pd.DataFrame(index=allsscind,columns=lois) #max 5-day MA impairment
allmdssc5pr = pd.DataFrame(index=allsscind,columns=lois) #max 5-day MA standardized impairment
allmdssc7df = pd.DataFrame(index=allsscind,columns=lois) #max 7-day MA impairment
allmdssc7pr = pd.DataFrame(index=allsscind,columns=lois) #max 7-day MA standardized impairment

#initialize mean tables
# by month across eco scenarios
mntmnesceco = pd.DataFrame(index=mntescind, columns=lois) #eco frequency reliability
mntmneschlc = pd.DataFrame(index=mntescind, columns=lois) #local human frequency reliability
mntmneschal = pd.DataFrame(index=mntescind, columns=lois) #all CA human frequency reliability
mntmnescdef = pd.DataFrame(index=mntescind, columns=lois) #impairment
mntmnescprp = pd.DataFrame(index=mntescind, columns=lois) #standardized impairment
mntmnesc3df = pd.DataFrame(index=mntescind, columns=lois) #max 3-day MA impairment
mntmnesc3pr = pd.DataFrame(index=mntescind, columns=lois) #max 3-day MA standardized impairment
mntmnesc5df = pd.DataFrame(index=mntescind, columns=lois) #max 5-day MA impairment
mntmnesc5pr = pd.DataFrame(index=mntescind, columns=lois) #max 5-day MA standardized impairment
mntmnesc7df = pd.DataFrame(index=mntescind, columns=lois) #max 7-day MA impairment
mntmnesc7pr = pd.DataFrame(index=mntescind, columns=lois) #max 7-day MA standardized impairment

# by month across human scenarios
mntmnssceco = pd.DataFrame(index=mntsscind,columns=lois) #eco frequency reliability
mntmnsschlc = pd.DataFrame(index=mntsscind,columns=lois) #local human frequency reliability
mntmnsschal = pd.DataFrame(index=mntsscind,columns=lois) #all CA human frequency reliability
mntmnsscdef = pd.DataFrame(index=mntsscind,columns=lois) #impairment
mntmnsscprp = pd.DataFrame(index=mntsscind,columns=lois) #standardized impairment
mntmnssc3df = pd.DataFrame(index=mntsscind,columns=lois) #max 3-day MA impairment
mntmnssc3pr = pd.DataFrame(index=mntsscind,columns=lois) #max 3-day MA standardized impairment
mntmnssc5df = pd.DataFrame(index=mntsscind,columns=lois) #max 5-day MA impairment
mntmnssc5pr = pd.DataFrame(index=mntsscind,columns=lois) #max 5-day MA standardized impairment
mntmnssc7df = pd.DataFrame(index=mntsscind,columns=lois) #max 7-day MA impairment
mntmnssc7pr = pd.DataFrame(index=mntsscind,columns=lois) #max 7-day MA standardized impairment

# by WMT across eco scenarios
wmtmnesceco = pd.DataFrame(index=wmtescind,columns=lois) #eco frequency reliability
wmtmneschlc = pd.DataFrame(index=wmtescind,columns=lois) #local human frequency reliability
wmtmneschal = pd.DataFrame(index=wmtescind,columns=lois) #all CA human frequency reliability
wmtmnescdef = pd.DataFrame(index=wmtescind,columns=lois) #impairment
wmtmnescprp = pd.DataFrame(index=wmtescind,columns=lois) #standardized impairment
wmtmnesc3df = pd.DataFrame(index=wmtescind,columns=lois) #max 3-day MA impairment
wmtmnesc3pr = pd.DataFrame(index=wmtescind,columns=lois) #max 3-day MA standardized impairment
wmtmnesc5df = pd.DataFrame(index=wmtescind,columns=lois) #max 5-day MA impairment
wmtmnesc5pr = pd.DataFrame(index=wmtescind,columns=lois) #max 5-day MA standardized impairment
wmtmnesc7df = pd.DataFrame(index=wmtescind,columns=lois) #max 7-day MA impairment
wmtmnesc7pr = pd.DataFrame(index=wmtescind,columns=lois) #max 7-day MA standardized impairment

# by WMT across human scenarios
wmtmnssceco = pd.DataFrame(index=wmtsscind,columns=lois) #eco frequency reliability
wmtmnsschlc = pd.DataFrame(index=wmtsscind,columns=lois) #local human frequency reliability
wmtmnsschal = pd.DataFrame(index=wmtsscind,columns=lois) #all CA human frequency reliability
wmtmnsscdef = pd.DataFrame(index=wmtsscind,columns=lois) #impairment
wmtmnsscprp = pd.DataFrame(index=wmtsscind,columns=lois) #standardized impairment
wmtmnssc3df = pd.DataFrame(index=wmtsscind,columns=lois) #max 3-day MA impairment
wmtmnssc3pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 3-day MA standardized impairment
wmtmnssc5df = pd.DataFrame(index=wmtsscind,columns=lois) #max 5-day MA impairment
wmtmnssc5pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 5-day MA standardized impairment
wmtmnssc7df = pd.DataFrame(index=wmtsscind,columns=lois) #max 7-day MA impairment
wmtmnssc7pr = pd.DataFrame(index=wmtsscind,columns=lois) #max 7-day MA standardized impairment

# over entire POR across eco scenarios
allmnesceco = pd.DataFrame(index=allescind, columns=lois) #eco frequency reliability
allmneschlc = pd.DataFrame(index=allescind, columns=lois) #local human frequency reliability
allmneschal = pd.DataFrame(index=allescind, columns=lois) #all CA human frequency reliability
allmnescdef = pd.DataFrame(index=allescind, columns=lois) #impairment
allmnescprp = pd.DataFrame(index=allescind, columns=lois) #standardized impairment
allmnesc3df = pd.DataFrame(index=allescind, columns=lois) #max 3-day MA impairment
allmnesc3pr = pd.DataFrame(index=allescind, columns=lois) #max 3-day MA standardized impairment
allmnesc5df = pd.DataFrame(index=allescind, columns=lois) #max 5-day MA impairment
allmnesc5pr = pd.DataFrame(index=allescind, columns=lois) #max 5-day MA standardized impairment
allmnesc7df = pd.DataFrame(index=allescind, columns=lois) #max 7-day MA impairment
allmnesc7pr = pd.DataFrame(index=allescind, columns=lois) #max 7-day MA standardized impairment

# over entire POR across human scenarios
allmnssceco = pd.DataFrame(index=allsscind,columns=lois) #eco frequency reliability
allmnsschlc = pd.DataFrame(index=allsscind,columns=lois) #local human frequency reliability
allmnsschal = pd.DataFrame(index=allsscind,columns=lois) #all CA human frequency reliability
allmnsscdef = pd.DataFrame(index=allsscind,columns=lois) #impairment
allmnsscprp = pd.DataFrame(index=allsscind,columns=lois) #standardized impairment
allmnssc3df = pd.DataFrame(index=allsscind,columns=lois) #max 3-day MA impairment
allmnssc3pr = pd.DataFrame(index=allsscind,columns=lois) #max 3-day MA standardized impairment
allmnssc5df = pd.DataFrame(index=allsscind,columns=lois) #max 5-day MA impairment
allmnssc5pr = pd.DataFrame(index=allsscind,columns=lois) #max 5-day MA standardized impairment
allmnssc7df = pd.DataFrame(index=allsscind,columns=lois) #max 7-day MA impairment
allmnssc7pr = pd.DataFrame(index=allsscind,columns=lois) #max 7-day MA standardized impairment

for l in lois: #loop through LOIs
    #status update
    lnum = str(np.where(lois == l)[0][0]+1)
    print('Processing LOI ' + str(int(l)) + ', ' + str(lnum) + '/' + str(len(lois)))
    loiday = wr.loc[wr['LOI'] == l, :] #filter daily performance by LOI
    scncomb = loiday.drop_duplicates(['SSC', 'ESC']).loc[:, ['SSC', 'ESC']].reset_index(drop=True) #get scenario combinations
    scncomb = scncomb.drop(scncomb.index[scncomb['SSC'] == 11]).reset_index(drop=True) #remove ssc 11 (no demands)
    scncomb = scncomb.drop(scncomb.index[scncomb['ESC'] == 1]).reset_index(drop=True) #remove esc 1 (no ift)
    if l in noepp:
        scncomb = scncomb.drop(scncomb.index[(scncomb['ESC'] >= 2) & (scncomb['ESC'] <= 7)]).reset_index(drop=True) #remove all EPPs if no EPPs exist for LOI
    escnum = np.sort(scncomb['ESC'].unique()) #get eco scenario numbers
    sscnum = np.sort(scncomb['SSC'].unique()) #get human scenario numbers

    for m in mnum: #loop through months
        #initialize scenario tables for current month
        mntcmpeco = pd.DataFrame(index=escnum, columns=sscnum) #eco frequency reliability
        mntcmphlc = pd.DataFrame(index=escnum, columns=sscnum) #local human frequency reliability
        mntcmphal = pd.DataFrame(index=escnum, columns=sscnum) #all CA human frequency reliability
        mntcmpdef = pd.DataFrame(index=escnum, columns=sscnum) #impairment
        mntcmpprp = pd.DataFrame(index=escnum, columns=sscnum) #standardized impairment
        mntcmp3df = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA impairment
        mntcmp3pr = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA standardized impairment
        mntcmp5df = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA impairment
        mntcmp5pr = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA standardized impairment
        mntcmp7df = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA impairment
        mntcmp7pr = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA standardized impairment
        mnam = cal.month_name[m] #convert month number to full name
        for s in scncomb.index: #loop through scenario combinations
            ssc = scncomb.loc[s, 'SSC'] #human scenario
            esc = scncomb.loc[s, 'ESC'] #ecological scenario
            # filter daily performance by scenario and month
            scnmnt = loiday.loc[(loiday['SSC'] == ssc) & (loiday['ESC'] == esc) & (loiday['month'] == m)]

            totdays = scnmnt['Eco Met'].count() #get total number of days
            mntcmpeco.loc[esc, ssc] = scnmnt['Eco Met'].sum()/totdays #calculate eco frequency
            mntcmphlc.loc[esc, ssc] = scnmnt['Hum Local Met'].sum() / totdays #calculate local human freq
            mntcmphal.loc[esc, ssc] = scnmnt['Hum All Met'].sum() / totdays #calculate all CA human freq
            mntcmpdef.loc[esc, ssc] = scnmnt['Impairment'].mean() #calculate mean impairment
            mntcmpprp.loc[esc, ssc] = scnmnt['Standardized Impairment'].mean() #calculate mean standardized impairment
            mntcmp3df.loc[esc, ssc] = scnmnt['3 Day Moving Avg Impairment'].max() #get max 3-day MA imp
            mntcmp3pr.loc[esc, ssc] = scnmnt['3 Day Moving Avg Standardized Impairment'].max() #get max 3-day MA stnd imp
            mntcmp5df.loc[esc, ssc] = scnmnt['5 Day Moving Avg Impairment'].max() #get max 5-day MA imp
            mntcmp5pr.loc[esc, ssc] = scnmnt['5 Day Moving Avg Standardized Impairment'].max() #get max 5-day MA stnd imp
            mntcmp7df.loc[esc, ssc] = scnmnt['7 Day Moving Avg Impairment'].max() #get max 7-day MA imp
            mntcmp7pr.loc[esc, ssc] = scnmnt['7 Day Moving Avg Standardized Impairment'].max() #get max 7-day MA stnd imp

        #call plotting functions that return mean and maxdiff values for monthly performance
        mntmdesceco, mntmnesceco, mntmdssceco, mntmnssceco = process_and_plot_table(mntcmpeco,
                                                                mntmdesceco, mntmnesceco, mntmdssceco, mntmnssceco, m, l, pltloc, 1, 1)
        mntmdeschlc, mntmneschlc, mntmdsschlc, mntmnsschlc = process_and_plot_table(mntcmphlc,
                                                                mntmdeschlc, mntmneschlc, mntmdsschlc, mntmnsschlc, m, l, pltloc, 2, 1)
        mntmdeschal, mntmneschal, mntmdsschal, mntmnsschal = process_and_plot_table(mntcmphal,
                                                                mntmdeschal, mntmneschal, mntmdsschal, mntmnsschal, m, l, pltloc, 3, 1)
        mntmdescdef, mntmnescdef, mntmdsscdef, mntmnsscdef = process_and_plot_table(mntcmpdef,
                                                                mntmdescdef, mntmnescdef, mntmdsscdef, mntmnsscdef, m, l, pltloc, 4, 1)
        mntmdescprp, mntmnescprp, mntmdsscprp, mntmnsscprp = process_and_plot_table(mntcmpprp,
                                                                mntmdescprp, mntmnescprp, mntmdsscprp, mntmnsscprp, m, l, pltloc, 5, 1)
        mntmdesc3df, mntmnesc3df, mntmdssc3df, mntmnssc3df = process_and_plot_table(mntcmp3df,
                                                                                    mntmdesc3df, mntmnesc3df,
                                                                                    mntmdssc3df, mntmnssc3df, m, l,
                                                                                    pltloc, 4, 1, defma = 3)
        mntmdesc3pr, mntmnesc3pr, mntmdssc3pr, mntmnssc3pr = process_and_plot_table(mntcmp3pr,
                                                                                    mntmdesc3pr, mntmnesc3pr,
                                                                                    mntmdssc3pr, mntmnssc3pr, m, l,
                                                                                    pltloc, 5, 1, defma = 3)
        mntmdesc5df, mntmnesc5df, mntmdssc5df, mntmnssc5df = process_and_plot_table(mntcmp5df,
                                                                                    mntmdesc5df, mntmnesc5df,
                                                                                    mntmdssc5df, mntmnssc5df, m, l,
                                                                                    pltloc, 4, 1, defma=5)
        mntmdesc5pr, mntmnesc5pr, mntmdssc5pr, mntmnssc5pr = process_and_plot_table(mntcmp5pr,
                                                                                    mntmdesc5pr, mntmnesc5pr,
                                                                                    mntmdssc5pr, mntmnssc5pr, m, l,
                                                                                    pltloc, 5, 1, defma=5)
        mntmdesc7df, mntmnesc7df, mntmdssc7df, mntmnssc7df = process_and_plot_table(mntcmp7df,
                                                                                    mntmdesc7df, mntmnesc7df,
                                                                                    mntmdssc7df, mntmnssc7df, m, l,
                                                                                    pltloc, 4, 1, defma = 7)
        mntmdesc7pr, mntmnesc7pr, mntmdssc7pr, mntmnssc7pr = process_and_plot_table(mntcmp7pr,
                                                                                    mntmdesc7pr, mntmnesc7pr,
                                                                                    mntmdssc7pr, mntmnssc7pr, m, l,
                                                                                    pltloc, 5, 1, defma = 7)
    for w in wmtnum: #loop through WMTs
        wmtcmpeco = pd.DataFrame(index=escnum, columns=sscnum) #eco frequency reliability
        wmtcmphlc = pd.DataFrame(index=escnum, columns=sscnum) #local human frequency reliability
        wmtcmphal = pd.DataFrame(index=escnum, columns=sscnum) #all CA human frequency reliability
        wmtcmpdef = pd.DataFrame(index=escnum, columns=sscnum) #impairment
        wmtcmpprp = pd.DataFrame(index=escnum, columns=sscnum) #standardized impairment
        wmtcmp3df = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA impairment
        wmtcmp3pr = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA standardized impairment
        wmtcmp5df = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA impairment
        wmtcmp5pr = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA standardized impairment
        wmtcmp7df = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA impairment
        wmtcmp7pr = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA standardized impairment
        for s in scncomb.index: #loop through scenario combinations
            ssc = scncomb.loc[s, 'SSC'] #human scenario
            esc = scncomb.loc[s, 'ESC'] #ecological scenario
            scnwmt = loiday.loc[(loiday['SSC'] == ssc) & (loiday['ESC'] == esc) & (loiday['WMT'] == w)] #filter by WMT and scenario

            totdays = scnwmt['Eco Met'].count() #get total number of days
            wmtcmpeco.loc[esc,ssc] = scnwmt['Eco Met'].sum()/totdays #calculate eco frequency
            wmtcmphlc.loc[esc, ssc] = scnwmt['Hum Local Met'].sum() / totdays #calculate local human freq
            wmtcmphal.loc[esc, ssc] = scnwmt['Hum All Met'].sum() / totdays #calculate all CA human freq
            wmtcmpdef.loc[esc, ssc] = scnwmt['Impairment'].mean() #calculate mean impairment
            wmtcmpprp.loc[esc, ssc] = scnwmt['Standardized Impairment'].mean() #calculate mean standardized impairment
            wmtcmp3df.loc[esc, ssc] = scnwmt['3 Day Moving Avg Impairment'].max() #get max 3-day MA imp
            wmtcmp3pr.loc[esc, ssc] = scnwmt['3 Day Moving Avg Standardized Impairment'].max() #get max 3-day MA stnd imp
            wmtcmp5df.loc[esc, ssc] = scnwmt['5 Day Moving Avg Impairment'].max() #get max 5-day MA imp
            wmtcmp5pr.loc[esc, ssc] = scnwmt['5 Day Moving Avg Standardized Impairment'].max() #get max 5-day MA stnd imp
            wmtcmp7df.loc[esc, ssc] = scnwmt['7 Day Moving Avg Impairment'].max() #get max 7-day MA imp
            wmtcmp7pr.loc[esc, ssc] = scnwmt['7 Day Moving Avg Standardized Impairment'].max() #get max 7-day MA stnd imp

        # call plotting functions that return mean and maxdiff values for WMT performance
        wmtmdesceco, wmtmnesceco, wmtmdssceco, wmtmnssceco = process_and_plot_table(wmtcmpeco,
                                                                wmtmdesceco, wmtmnesceco, wmtmdssceco, wmtmnssceco, w, l, pltloc, 1, 2)
        wmtmdeschlc, wmtmneschlc, wmtmdsschlc, wmtmnsschlc = process_and_plot_table(wmtcmphlc,
                                                                wmtmdeschlc, wmtmneschlc, wmtmdsschlc, wmtmnsschlc, w, l, pltloc, 2, 2)
        wmtmdeschal, wmtmneschal, wmtmdsschal, wmtmnsschal = process_and_plot_table(wmtcmphal,
                                                                wmtmdeschal, wmtmneschal, wmtmdsschal, wmtmnsschal, w, l, pltloc, 3, 2)
        wmtmdescdef, wmtmnescdef, wmtmdsscdef, wmtmnsscdef = process_and_plot_table(wmtcmpdef,
                                                                wmtmdescdef, wmtmnescdef, wmtmdsscdef, wmtmnsscdef, w, l, pltloc, 4, 2)
        wmtmdescprp, wmtmnescprp, wmtmdsscprp, wmtmnsscprp = process_and_plot_table(wmtcmpprp,
                                                                wmtmdescprp, wmtmnescprp, wmtmdsscprp, wmtmnsscprp, w, l, pltloc, 5, 2)
        wmtmdesc3df, wmtmnesc3df, wmtmdssc3df, wmtmnssc3df = process_and_plot_table(wmtcmp3df,
                                                                                    wmtmdesc3df, wmtmnesc3df,
                                                                                    wmtmdssc3df, wmtmnssc3df, w, l,
                                                                                    pltloc, 4, 2, defma=3)
        wmtmdesc3pr, wmtmnesc3pr, wmtmdssc3pr, wmtmnssc3pr = process_and_plot_table(wmtcmp3pr,
                                                                                    wmtmdesc3pr, wmtmnesc3pr,
                                                                                    wmtmdssc3pr, wmtmnssc3pr, w, l,
                                                                                    pltloc, 5, 2, defma=3)
        wmtmdesc5df, wmtmnesc5df, wmtmdssc5df, wmtmnssc5df = process_and_plot_table(wmtcmp5df,
                                                                                    wmtmdesc5df, wmtmnesc5df,
                                                                                    wmtmdssc5df, wmtmnssc5df, w, l,
                                                                                    pltloc, 4, 2, defma=5)
        wmtmdesc5pr, wmtmnesc5pr, wmtmdssc5pr, wmtmnssc5pr = process_and_plot_table(wmtcmp5pr,
                                                                                    wmtmdesc5pr, wmtmnesc5pr,
                                                                                    wmtmdssc5pr, wmtmnssc5pr, w, l,
                                                                                    pltloc, 5, 2, defma=5)
        wmtmdesc7df, wmtmnesc7df, wmtmdssc7df, wmtmnssc7df = process_and_plot_table(wmtcmp7df,
                                                                                    wmtmdesc7df, wmtmnesc7df,
                                                                                    wmtmdssc7df, wmtmnssc7df, w, l,
                                                                                    pltloc, 4, 2, defma=7)
        wmtmdesc7pr, wmtmnesc7pr, wmtmdssc7pr, wmtmnssc7pr = process_and_plot_table(wmtcmp7pr,
                                                                                    wmtmdesc7pr, wmtmnesc7pr,
                                                                                    wmtmdssc7pr, wmtmnssc7pr, w, l,
                                                                                    pltloc, 5, 2, defma=7)

    #initialize performance across entire POR
    allcmpeco = pd.DataFrame(index=escnum, columns=sscnum) #eco frequency reliability
    allcmphlc = pd.DataFrame(index=escnum, columns=sscnum) #local human frequency reliability
    allcmphal = pd.DataFrame(index=escnum, columns=sscnum) #all CA human frequency reliability
    allcmpdef = pd.DataFrame(index=escnum, columns=sscnum) #impairment
    allcmpprp = pd.DataFrame(index=escnum, columns=sscnum) #standardized impairment
    allcmp3df = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA impairment
    allcmp3pr = pd.DataFrame(index=escnum, columns=sscnum) #max 3-day MA standardized impairment
    allcmp5df = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA impairment
    allcmp5pr = pd.DataFrame(index=escnum, columns=sscnum) #max 5-day MA standardized impairment
    allcmp7df = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA impairment
    allcmp7pr = pd.DataFrame(index=escnum, columns=sscnum) #max 7-day MA standardized impairment
    for s in scncomb.index: #loop through scenario combinations
        ssc = scncomb.loc[s, 'SSC'] #human scenario
        esc = scncomb.loc[s, 'ESC'] #ecological scenario
        scnall = loiday.loc[(loiday['SSC'] == ssc) & (loiday['ESC'] == esc)] #filter by scenarios

        totdays = scnall['Eco Met'].count() #get total number of days
        allcmpeco.loc[esc, ssc] = scnall['Eco Met'].sum() / totdays #calculate eco frequency
        allcmphlc.loc[esc, ssc] = scnall['Hum Local Met'].sum() / totdays #calculate local human freq
        allcmphal.loc[esc, ssc] = scnall['Hum All Met'].sum() / totdays #calculate all CA human freq
        allcmpdef.loc[esc, ssc] = scnall['Impairment'].mean() #calculate mean impairment
        allcmpprp.loc[esc, ssc] = scnall['Standardized Impairment'].mean() #calculate mean standardized impairment
        allcmp3df.loc[esc, ssc] = scnall['3 Day Moving Avg Impairment'].max() #get max 3-day MA imp
        allcmp3pr.loc[esc, ssc] = scnall['3 Day Moving Avg Standardized Impairment'].max() #get max 3-day MA stnd imp
        allcmp5df.loc[esc, ssc] = scnall['5 Day Moving Avg Impairment'].max() #get max 5-day MA imp
        allcmp5pr.loc[esc, ssc] = scnall['5 Day Moving Avg Standardized Impairment'].max() #get max 5-day MA stnd imp
        allcmp7df.loc[esc, ssc] = scnall['7 Day Moving Avg Impairment'].max() #get max 7-day MA imp
        allcmp7pr.loc[esc, ssc] = scnall['7 Day Moving Avg Standardized Impairment'].max() #get max 7-day MA stnd imp

    # call plotting functions that return mean and maxdiff values for performance across POR
    allmdesceco, allmnesceco, allmdssceco, allmnssceco = process_and_plot_table(allcmpeco,
                                                                                allmdesceco, allmnesceco, allmdssceco,
                                                                                allmnssceco, 0, l, pltloc, 1, 3)
    allmdeschlc, allmneschlc, allmdsschlc, allmnsschlc = process_and_plot_table(allcmphlc,
                                                                                allmdeschlc, allmneschlc, allmdsschlc,
                                                                                allmnsschlc, 0, l, pltloc, 2, 3)
    allmdeschal, allmneschal, allmdsschal, allmnsschal = process_and_plot_table(allcmphal,
                                                                                allmdeschal, allmneschal, allmdsschal,
                                                                                allmnsschal, 0, l, pltloc, 3, 3)
    allmdescdef, allmnescdef, allmdsscdef, allmnsscdef = process_and_plot_table(allcmpdef,
                                                                                allmdescdef, allmnescdef, allmdsscdef,
                                                                                allmnsscdef, 0, l, pltloc, 4, 3)
    allmdescprp, allmnescprp, allmdsscprp, allmnsscprp = process_and_plot_table(allcmpprp,
                                                                                allmdescprp, allmnescprp, allmdsscprp,
                                                                                allmnsscprp, 0, l, pltloc, 5, 3)
    allmdesc3df, allmnesc3df, allmdssc3df, allmnssc3df = process_and_plot_table(allcmp3df,
                                                                                allmdesc3df, allmnesc3df,
                                                                                allmdssc3df, allmnssc3df, 0, l,
                                                                                pltloc, 4, 3, defma=3)
    allmdesc3pr, allmnesc3pr, allmdssc3pr, allmnssc3pr = process_and_plot_table(allcmp3pr,
                                                                                allmdesc3pr, allmnesc3pr,
                                                                                allmdssc3pr, allmnssc3pr, 0, l,
                                                                                pltloc, 5, 3, defma=3)
    allmdesc5df, allmnesc5df, allmdssc5df, allmnssc5df = process_and_plot_table(allcmp5df,
                                                                                allmdesc5df, allmnesc5df,
                                                                                allmdssc5df, allmnssc5df, 0, l,
                                                                                pltloc, 4, 3, defma=5)
    allmdesc5pr, allmnesc5pr, allmdssc5pr, allmnssc5pr = process_and_plot_table(allcmp5pr,
                                                                                allmdesc5pr, allmnesc5pr,
                                                                                allmdssc5pr, allmnssc5pr, 0, l,
                                                                                pltloc, 5, 3, defma=5)
    allmdesc7df, allmnesc7df, allmdssc7df, allmnssc7df = process_and_plot_table(allcmp7df,
                                                                                allmdesc7df, allmnesc7df,
                                                                                allmdssc7df, allmnssc7df, 0, l,
                                                                                pltloc, 4, 3, defma=7)
    allmdesc7pr, allmnesc7pr, allmdssc7pr, allmnssc7pr = process_and_plot_table(allcmp7pr,
                                                                                allmdesc7pr, allmnesc7pr,
                                                                                allmdssc7pr, allmnssc7pr, 0, l,
                                                                                pltloc, 5, 3, defma=7)

#after all LOIs done, plot max diff and mean tables against LOI
print('Plotting all LOI Max Differences and means')
for m in mnum: #loop through month
    esclab = get_scn_name(esc=mntmdesceco.loc[m, :].index) #eco scenario labels
    ssclab = get_scn_name(ssc=mntmdssceco.loc[m, :].index) #human scenario labels
    loilab = mntmdesceco.columns.astype(int) #format LOI as int to remove decimal place in label

    #plot mean across human scenarios in each month
    plot_md_mn_table(mntmnssceco, loilab, ssclab, 1, 1, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnsschlc, loilab, ssclab, 2, 1, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnsschal, loilab, ssclab, 3, 1, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnsscdef, loilab, ssclab, 4, 1, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnsscprp, loilab, ssclab, 5, 1, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnssc3df, loilab, ssclab, 4, 1, 1, m, 1, pltloc, defma=3)
    plot_md_mn_table(mntmnssc3pr, loilab, ssclab, 5, 1, 1, m, 1, pltloc, defma=3)
    plot_md_mn_table(mntmnssc5df, loilab, ssclab, 4, 1, 1, m, 1, pltloc, defma=5)
    plot_md_mn_table(mntmnssc5pr, loilab, ssclab, 5, 1, 1, m, 1, pltloc, defma=5)
    plot_md_mn_table(mntmnssc7df, loilab, ssclab, 4, 1, 1, m, 1, pltloc, defma=7)
    plot_md_mn_table(mntmnssc7pr, loilab, ssclab, 5, 1, 1, m, 1, pltloc, defma=7)

    # plot mean across eco scenarios in each month
    plot_md_mn_table(mntmnesceco, loilab, esclab, 1, 2, 1, m, 1, pltloc)
    plot_md_mn_table(mntmneschlc, loilab, esclab, 2, 2, 1, m, 1, pltloc)
    plot_md_mn_table(mntmneschal, loilab, esclab, 3, 2, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnescdef, loilab, esclab, 4, 2, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnescprp, loilab, esclab, 5, 2, 1, m, 1, pltloc)
    plot_md_mn_table(mntmnesc3df, loilab, ssclab, 4, 2, 1, m, 1, pltloc, defma=3)
    plot_md_mn_table(mntmnesc3pr, loilab, ssclab, 5, 2, 1, m, 1, pltloc, defma=3)
    plot_md_mn_table(mntmnesc5df, loilab, ssclab, 4, 2, 1, m, 1, pltloc, defma=5)
    plot_md_mn_table(mntmnesc5pr, loilab, ssclab, 5, 2, 1, m, 1, pltloc, defma=5)
    plot_md_mn_table(mntmnesc7df, loilab, ssclab, 4, 2, 1, m, 1, pltloc, defma=7)
    plot_md_mn_table(mntmnesc7pr, loilab, ssclab, 5, 2, 1, m, 1, pltloc, defma=7)

    # plot max diff across human scenarios in each month
    plot_md_mn_table(mntmdssceco, loilab, ssclab, 1, 1, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdsschlc, loilab, ssclab, 2, 1, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdsschal, loilab, ssclab, 3, 1, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdsscdef, loilab, ssclab, 4, 1, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdsscprp, loilab, ssclab, 5, 1, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdssc3df, loilab, ssclab, 4, 1, 1, m, 2, pltloc, defma=3)
    plot_md_mn_table(mntmdssc3pr, loilab, ssclab, 5, 1, 1, m, 2, pltloc, defma=3)
    plot_md_mn_table(mntmdssc5df, loilab, ssclab, 4, 1, 1, m, 2, pltloc, defma=5)
    plot_md_mn_table(mntmdssc5pr, loilab, ssclab, 5, 1, 1, m, 2, pltloc, defma=5)
    plot_md_mn_table(mntmdssc7df, loilab, ssclab, 4, 1, 1, m, 2, pltloc, defma=7)
    plot_md_mn_table(mntmdssc7pr, loilab, ssclab, 5, 1, 1, m, 2, pltloc, defma=7)

    # plot max diff across eco scenarios in each month
    plot_md_mn_table(mntmdesceco, loilab, esclab, 1, 2, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdeschlc, loilab, esclab, 2, 2, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdeschal, loilab, esclab, 3, 2, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdescdef, loilab, esclab, 4, 2, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdescprp, loilab, esclab, 5, 2, 1, m, 2, pltloc)
    plot_md_mn_table(mntmdesc3df, loilab, ssclab, 4, 2, 1, m, 2, pltloc, defma=3)
    plot_md_mn_table(mntmdesc3pr, loilab, ssclab, 5, 2, 1, m, 2, pltloc, defma=3)
    plot_md_mn_table(mntmdesc5df, loilab, ssclab, 4, 2, 1, m, 2, pltloc, defma=5)
    plot_md_mn_table(mntmdesc5pr, loilab, ssclab, 5, 2, 1, m, 2, pltloc, defma=5)
    plot_md_mn_table(mntmdesc7df, loilab, ssclab, 4, 2, 1, m, 2, pltloc, defma=7)
    plot_md_mn_table(mntmdesc7pr, loilab, ssclab, 5, 2, 1, m, 2, pltloc, defma=7)
    
for w in wmtnum: #loop through WMTs
    esclab = get_scn_name(esc=wmtmdesceco.loc[w,:].index)
    ssclab = get_scn_name(ssc=wmtmdssceco.loc[w, :].index)
    loilab = wmtmdesceco.columns.astype(int)

    # plot mean across human scenarios in each WMT
    plot_md_mn_table(wmtmnssceco, loilab, ssclab, 1, 1, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnsschlc, loilab, ssclab, 2, 1, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnsschal, loilab, ssclab, 3, 1, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnsscdef, loilab, ssclab, 4, 1, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnsscprp, loilab, ssclab, 5, 1, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnssc3df, loilab, ssclab, 4, 1, 2, w, 1, pltloc, defma=3)
    plot_md_mn_table(wmtmnssc3pr, loilab, ssclab, 5, 1, 2, w, 1, pltloc, defma=3)
    plot_md_mn_table(wmtmnssc5df, loilab, ssclab, 4, 1, 2, w, 1, pltloc, defma=5)
    plot_md_mn_table(wmtmnssc5pr, loilab, ssclab, 5, 1, 2, w, 1, pltloc, defma=5)
    plot_md_mn_table(wmtmnssc7df, loilab, ssclab, 4, 1, 2, w, 1, pltloc, defma=7)
    plot_md_mn_table(wmtmnssc7pr, loilab, ssclab, 5, 1, 2, w, 1, pltloc, defma=7)

    # plot mean across eco scenarios in each WMT
    plot_md_mn_table(wmtmnesceco, loilab, esclab, 1, 2, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmneschlc, loilab, esclab, 2, 2, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmneschal, loilab, esclab, 3, 2, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnescdef, loilab, esclab, 4, 2, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnescprp, loilab, esclab, 5, 2, 2, w, 1, pltloc)
    plot_md_mn_table(wmtmnesc3df, loilab, ssclab, 4, 2, 2, w, 1, pltloc, defma=3)
    plot_md_mn_table(wmtmnesc3pr, loilab, ssclab, 5, 2, 2, w, 1, pltloc, defma=3)
    plot_md_mn_table(wmtmnesc5df, loilab, ssclab, 4, 2, 2, w, 1, pltloc, defma=5)
    plot_md_mn_table(wmtmnesc5pr, loilab, ssclab, 5, 2, 2, w, 1, pltloc, defma=5)
    plot_md_mn_table(wmtmnesc7df, loilab, ssclab, 4, 2, 2, w, 1, pltloc, defma=7)
    plot_md_mn_table(wmtmnesc7pr, loilab, ssclab, 5, 2, 2, w, 1, pltloc, defma=7)

    # plot max diff across human scenarios in each WMT
    plot_md_mn_table(wmtmdssceco, loilab, ssclab, 1, 1, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdsschlc, loilab, ssclab, 2, 1, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdsschal, loilab, ssclab, 3, 1, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdsscdef, loilab, ssclab, 4, 1, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdsscprp, loilab, ssclab, 5, 1, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdssc3df, loilab, ssclab, 4, 1, 2, w, 2, pltloc, defma=3)
    plot_md_mn_table(wmtmdssc3pr, loilab, ssclab, 5, 1, 2, w, 2, pltloc, defma=3)
    plot_md_mn_table(wmtmdssc5df, loilab, ssclab, 4, 1, 2, w, 2, pltloc, defma=5)
    plot_md_mn_table(wmtmdssc5pr, loilab, ssclab, 5, 1, 2, w, 2, pltloc, defma=5)
    plot_md_mn_table(wmtmdssc7df, loilab, ssclab, 4, 1, 2, w, 2, pltloc, defma=7)
    plot_md_mn_table(wmtmdssc7pr, loilab, ssclab, 5, 1, 2, w, 2, pltloc, defma=7)

    # plot max diff across eco scenarios in each WMT
    plot_md_mn_table(wmtmdesceco, loilab, esclab, 1, 2, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdeschlc, loilab, esclab, 2, 2, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdeschal, loilab, esclab, 3, 2, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdescdef, loilab, esclab, 4, 2, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdescprp, loilab, esclab, 5, 2, 2, w, 2, pltloc)
    plot_md_mn_table(wmtmdesc3df, loilab, ssclab, 4, 2, 2, w, 2, pltloc, defma=3)
    plot_md_mn_table(wmtmdesc3pr, loilab, ssclab, 5, 2, 2, w, 2, pltloc, defma=3)
    plot_md_mn_table(wmtmdesc5df, loilab, ssclab, 4, 2, 2, w, 2, pltloc, defma=5)
    plot_md_mn_table(wmtmdesc5pr, loilab, ssclab, 5, 2, 2, w, 2, pltloc, defma=5)
    plot_md_mn_table(wmtmdesc7df, loilab, ssclab, 4, 2, 2, w, 2, pltloc, defma=7)
    plot_md_mn_table(wmtmdesc7pr, loilab, ssclab, 5, 2, 2, w, 2, pltloc, defma=7)

#finally do entire POR
esclab = get_scn_name(esc=allmdesceco.index)
ssclab = get_scn_name(ssc=allmdssceco.index)
loilab = allmdesceco.columns.astype(int)

plot_md_mn_table(allmnssceco, loilab, ssclab, 1, 1, 3, 0, 1, pltloc)
plot_md_mn_table(allmnsschlc, loilab, ssclab, 2, 1, 3, 0, 1, pltloc)
plot_md_mn_table(allmnsschal, loilab, ssclab, 3, 1, 3, 0, 1, pltloc)
plot_md_mn_table(allmnsscdef, loilab, ssclab, 4, 1, 3, 0, 1, pltloc)
plot_md_mn_table(allmnsscprp, loilab, ssclab, 5, 1, 3, 0, 1, pltloc)
plot_md_mn_table(allmnssc3df, loilab, ssclab, 4, 1, 3, 0, 1, pltloc, defma=3)
plot_md_mn_table(allmnssc3pr, loilab, ssclab, 5, 1, 3, 0, 1, pltloc, defma=3)
plot_md_mn_table(allmnssc5df, loilab, ssclab, 4, 1, 3, 0, 1, pltloc, defma=5)
plot_md_mn_table(allmnssc5pr, loilab, ssclab, 5, 1, 3, 0, 1, pltloc, defma=5)
plot_md_mn_table(allmnssc7df, loilab, ssclab, 4, 1, 3, 0, 1, pltloc, defma=7)
plot_md_mn_table(allmnssc7pr, loilab, ssclab, 5, 1, 3, 0, 1, pltloc, defma=7)

plot_md_mn_table(allmnesceco, loilab, esclab, 1, 2, 3, 0, 1, pltloc)
plot_md_mn_table(allmneschlc, loilab, esclab, 2, 2, 3, 0, 1, pltloc)
plot_md_mn_table(allmneschal, loilab, esclab, 3, 2, 3, 0, 1, pltloc)
plot_md_mn_table(allmnescdef, loilab, esclab, 4, 2, 3, 0, 1, pltloc)
plot_md_mn_table(allmnescprp, loilab, esclab, 5, 2, 3, 0, 1, pltloc)
plot_md_mn_table(allmnesc3df, loilab, ssclab, 4, 2, 3, 0, 1, pltloc, defma=3)
plot_md_mn_table(allmnesc3pr, loilab, ssclab, 5, 2, 3, 0, 1, pltloc, defma=3)
plot_md_mn_table(allmnesc5df, loilab, ssclab, 4, 2, 3, 0, 1, pltloc, defma=5)
plot_md_mn_table(allmnesc5pr, loilab, ssclab, 5, 2, 3, 0, 1, pltloc, defma=5)
plot_md_mn_table(allmnesc7df, loilab, ssclab, 4, 2, 3, 0, 1, pltloc, defma=7)
plot_md_mn_table(allmnesc7pr, loilab, ssclab, 5, 2, 3, 0, 1, pltloc, defma=7)

plot_md_mn_table(allmdssceco, loilab, ssclab, 1, 1, 3, 0, 2, pltloc)
plot_md_mn_table(allmdsschlc, loilab, ssclab, 2, 1, 3, 0, 2, pltloc)
plot_md_mn_table(allmdsschal, loilab, ssclab, 3, 1, 3, 0, 2, pltloc)
plot_md_mn_table(allmdsscdef, loilab, ssclab, 4, 1, 3, 0, 2, pltloc)
plot_md_mn_table(allmdsscprp, loilab, ssclab, 5, 1, 3, 0, 2, pltloc)
plot_md_mn_table(allmdssc3df, loilab, ssclab, 4, 1, 3, 0, 2, pltloc, defma=3)
plot_md_mn_table(allmdssc3pr, loilab, ssclab, 5, 1, 3, 0, 2, pltloc, defma=3)
plot_md_mn_table(allmdssc5df, loilab, ssclab, 4, 1, 3, 0, 2, pltloc, defma=5)
plot_md_mn_table(allmdssc5pr, loilab, ssclab, 5, 1, 3, 0, 2, pltloc, defma=5)
plot_md_mn_table(allmdssc7df, loilab, ssclab, 4, 1, 3, 0, 2, pltloc, defma=7)
plot_md_mn_table(allmdssc7pr, loilab, ssclab, 5, 1, 3, 0, 2, pltloc, defma=7)

plot_md_mn_table(allmdesceco, loilab, esclab, 1, 2, 3, 0, 2, pltloc)
plot_md_mn_table(allmdeschlc, loilab, esclab, 2, 2, 3, 0, 2, pltloc)
plot_md_mn_table(allmdeschal, loilab, esclab, 3, 2, 3, 0, 2, pltloc)
plot_md_mn_table(allmdescdef, loilab, esclab, 4, 2, 3, 0, 2, pltloc)
plot_md_mn_table(allmdescprp, loilab, esclab, 5, 2, 3, 0, 2, pltloc)
plot_md_mn_table(allmdesc3df, loilab, ssclab, 4, 2, 3, 0, 2, pltloc, defma=3)
plot_md_mn_table(allmdesc3pr, loilab, ssclab, 5, 2, 3, 0, 2, pltloc, defma=3)
plot_md_mn_table(allmdesc5df, loilab, ssclab, 4, 2, 3, 0, 2, pltloc, defma=5)
plot_md_mn_table(allmdesc5pr, loilab, ssclab, 5, 2, 3, 0, 2, pltloc, defma=5)
plot_md_mn_table(allmdesc7df, loilab, ssclab, 4, 2, 3, 0, 2, pltloc, defma=7)
plot_md_mn_table(allmdesc7pr, loilab, ssclab, 5, 2, 3, 0, 2, pltloc, defma=7)