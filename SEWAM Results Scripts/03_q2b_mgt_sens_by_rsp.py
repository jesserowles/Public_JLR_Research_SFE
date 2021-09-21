#The purpose of this script is to answer questions 2b by plotting relative performance against RSP:
# 2b. Do the sensitivity relationships from 2a between human scenarios
# and performance vary with channel reach settings?
import sys
sys.path.insert(1,'./SEWAM Results Scripts')
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import pandas as pd
import seaborn as sns
from lookup_scenarios import get_scn_name
from weap_results_v2 import read_weap_results
import numpy as np
from plot_performance import plot_change_from_bl_numrsp, plot_change_from_bl_catrsp
import matplotlib.cm as cm

pltloc = './SEWAM Results Analyses/Question 2/2b - Trends Against RSP/' #set plot location

wr, loitab = read_weap_results(recalc=0,ltonly = 1) #read performance by LOI table
#read RSP table
rsptab = pd.read_csv('./Reference Files/Master RSP List.csv',index_col=0)
rspind = (~np.isin(rsptab.columns,['LOI','dnLOI','Lat','Lon'])) #get indices of RSP
numrsp = rsptab.columns[rspind & (rsptab.dtypes == 'float64').get_values()] #list of numeric RSPs
catrsp = rsptab.columns[rspind & ~(rsptab.dtypes == 'float64').get_values()] #list of categorical RSPs
do_all_metrics = 1 #set = 1 to re run for every metric, otherwise only re-runs for ones that don't have folders made
allscncomb = loitab.drop_duplicates(['SSC', 'ESC']).loc[:, ['SSC', 'ESC']] #get all scenario combinations
#remove eco scenario 1 (no IFT) and human scenario 1 (baseline)
relscncomb = allscncomb.loc[~((allscncomb['SSC'] == 1) | (allscncomb['ESC'] == 1)), :].reset_index()
# allmets = loitab.drop(['LOI','SSC','ESC'],axis=1).columns #do this to run on every performance metric (takes a very long time)
#or do for selected metrics by defining them here:
allmets = [
    "Entire POR Frequency of Days for Ecological Demands",
						 # "Entire POR Frequency of Days for All Upstream Human Demands",
						 "Entire POR Mean Standardized Impairment"
						 # "Entire POR Standardized Impairment 3 Day Moving Avg Max",
						 # "Entire POR Standardized Impairment 5 Day Moving Avg Max",
						 # "Entire POR Standardized Impairment 7 Day Moving Avg Max",
						 # "January Frequency of Days for Ecological Demands",
						 # "January Frequency of Days for All Upstream Human Demands",
						 # "January Mean Standardized Impairment",
						 # "January Standardized Impairment 3 Day Moving Avg Max",
						 # "January Standardized Impairment 5 Day Moving Avg Max",
						 # "January Standardized Impairment 7 Day Moving Avg Max",
						 # "July Frequency of Days for Ecological Demands",
						 # "July Frequency of Days for All Upstream Human Demands",
						 # "July Mean Standardized Impairment",
						 # "July Standardized Impairment 3 Day Moving Avg Max",
						 # "July Standardized Impairment 5 Day Moving Avg Max",
						 # "July Standardized Impairment 7 Day Moving Avg Max"
]
for metric in allmets: #loop through metrics
    mnum = list(allmets).index(metric) + 1 #get metric number in list of metrics for status updates
    mtrloc = pltloc + metric + '/' #folder name
    if not os.path.isdir(mtrloc) or do_all_metrics == 1: #only do if folder doesn't exist or do_all_metrics= 1
        if not os.path.isdir(mtrloc):
            os.mkdir(mtrloc) #create folder if it doesn't exist yet
        print('Processing "' + metric + '", ' + str(mnum) + '/' + str(len(allmets))) #status update
        lois = list(loitab['LOI'].unique().astype(int)) # list of LOIs

        ptab = pd.DataFrame(columns=['SSC','ESC']+lois) #initalize performance table by location and scenario
        for l in lois: #loop through LOIs
            for s in relscncomb.index: #loop through relative scenario combinations
                ssc = relscncomb.loc[s,'SSC'] #human scenario
                esc = relscncomb.loc[s,'ESC'] #eco scenario
                cpscn = (loitab['SSC'] == ssc) & (loitab['ESC'] == esc) & (loitab['LOI'] == l) #get performance for scenario combination
                blscn = (loitab['SSC'] == 1) & (loitab['ESC'] == esc) & (loitab['LOI'] == l) #get performance for baseline
                pchange = (loitab.loc[cpscn,metric].get_values() - loitab.loc[blscn,metric].get_values())[0] #calculate relative perf
                ptab.loc[s, ['SSC','ESC',l]] = [ssc,esc,pchange] #record relative performance in table

        alleco = ptab.astype(float).groupby('SSC').mean() #calculate mean across all eco scenarios
        alleco['ESC'] = 16 #set eco scenario value to 16 (one more than max value of 15
        #set index to human scenario and remove eco scenario column
        alleco['SSC'] = alleco.index
        ptab = ptab.append(alleco,sort=False).reset_index(drop=True)
        allesc = ptab['ESC'].unique()
        for a in allesc: #loop through all ecoscenarios to make plots
            #filter by current eco scenario
            cesc = ptab.loc[ptab['ESC'] == a, :]
            cesc.index = cesc['SSC']

            for r in numrsp: #loop through numeric RSPs for plotting
                justp = cesc.drop(['SSC', 'ESC'], axis=1).T #remove scenario columns and reformat
                plot_change_from_bl_numrsp(justp, a, r, rsptab, metric, mtrloc) #plotting function

            justp = cesc.drop(['SSC', 'ESC'], axis=1).T#remove scenario columns and reformat
            plot_change_from_bl_catrsp(justp, a, catrsp, rsptab, metric, mtrloc) #plotting function
    else: #otherwise, skip metric
        print('Skipping "' + metric + '", ' + str(mnum) + '/' + str(len(allmets)) + ' - Already Done')