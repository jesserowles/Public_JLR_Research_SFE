#The purpose of this script is to answer questions 2a using violin and batr plots:
# 2a. How sensitive is ecological performance to changes in water demand and storage?
# In general, are there model variables that have larger effects on ecological
# performance than others?
#

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
from plot_performance import plot_change_from_baseline

pltloc = './SEWAM Results Analyses/Question 2/2a - General Trends/' #plot location
do_all = 1 #if set to 1 make all folders regardless of if they've been done before. Otherwise don't make new folders
wr, loitab = read_weap_results(recalc=0,ltonly = 1) #read in performance by LOI table

allscncomb = loitab.drop_duplicates(['SSC', 'ESC']).loc[:, ['SSC', 'ESC']] # get all scenario combinations
#remove scenario combinations with human scenario of 1 (baseline) or eco scenario of 1 (no IFT)
relscncomb = allscncomb.loc[~((allscncomb['SSC'] == 1) | (allscncomb['ESC'] == 1)), :].reset_index()

#Run for all perofmance metrics:
# allmets = loitab.drop(['LOI','SSC','ESC'],axis=1).columns #do this to run on every performance metric (takes awhile)
#or run for selected metrics:
allmets = [
    "Entire POR Frequency of Days for Ecological Demands",
						 "Entire POR Frequency of Days for All Upstream Human Demands",
						 "Entire POR Mean Standardized Impairment",
						 "Entire POR Standardized Impairment 3 Day Moving Avg Max",
						 "Entire POR Standardized Impairment 5 Day Moving Avg Max",
						 "Entire POR Standardized Impairment 7 Day Moving Avg Max",
						 "January Frequency of Days for Ecological Demands",
						 "January Frequency of Days for All Upstream Human Demands",
						 "January Mean Standardized Impairment",
						 "January Standardized Impairment 3 Day Moving Avg Max",
						 "January Standardized Impairment 5 Day Moving Avg Max",
						 "January Standardized Impairment 7 Day Moving Avg Max",
						 "July Frequency of Days for Ecological Demands",
						 "July Frequency of Days for All Upstream Human Demands",
						 "July Mean Standardized Impairment",
						 "July Standardized Impairment 3 Day Moving Avg Max",
						 "July Standardized Impairment 5 Day Moving Avg Max",
						 "July Standardized Impairment 7 Day Moving Avg Max"
           ]

for metric in allmets: #loop through metrics
    mnum = list(allmets).index(metric) + 1 #metric number
    mtrloc = pltloc + metric + '/' #create string containing new folder
    if (not os.path.isdir(mtrloc)) or (do_all == 1): #only generate plots if not already done or if do_all = 1
        print('Processing "' + metric + '", ' + str(mnum) + '/' + str(len(allmets))) #print status update

        if (not os.path.isdir(mtrloc)):
            os.mkdir(mtrloc) #create folder if not already made
        lois = list(loitab['LOI'].unique().astype(int)) #list of LOIs
        ptab = pd.DataFrame(columns=['SSC','ESC']+lois) #performance table
        for l in lois: #loop through LOIs
            for s in relscncomb.index: #loop through relative scenario combinations
                ssc = relscncomb.loc[s,'SSC'] #record human scenario
                esc = relscncomb.loc[s,'ESC'] #record eco scenario
                cpscn = (loitab['SSC'] == ssc) & (loitab['ESC'] == esc) & (loitab['LOI'] == l) #current scenario combination
                blscn = (loitab['SSC'] == 1) & (loitab['ESC'] == esc) & (loitab['LOI'] == l) #baseline human scenario for given eco scenario
                pchange = (loitab.loc[cpscn,metric].get_values() - loitab.loc[blscn,metric].get_values())[0] #relative performance value
                ptab.loc[s, ['SSC','ESC',l]] = [ssc,esc,pchange] #record relative performance for LOI and scenario

        allesc = ptab['ESC'].unique() #loop through eco scenarios for plot
        for a in allesc:
            cesc = ptab.loc[ptab['ESC'] == a,:] #filter by eco scenario
            #set human scenario as index, and remove scenario columns
            cesc.index = cesc['SSC']
            justp = cesc.drop(['SSC','ESC'],axis=1)
            plot_change_from_baseline(justp, a, metric, mtrloc) #plotting function

        #Generate plots of average over all LOIs and all Ecological scenarios
        allavgeco = ptab.astype(float).groupby('SSC').mean().drop('ESC',axis=1) #calculate mean relative performance and format table
        plot_change_from_baseline(allavgeco,0,metric,mtrloc) #plotting function
    else: #otherwise, skip metric
        print('Skipping "' + metric + '", ' + str(mnum) + '/' + str(len(allmets)),', already done')