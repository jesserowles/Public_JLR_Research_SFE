#The purpose of this script is to answer question 3 by creating performance
# surfaces against month and WMT:
#•	3. How do climate conditions affect ecological and
# human demand performance at different locations? Alternatively,
# how do ecological and human demand performance vary with
# climate conditions?
import sys
sys.path.insert(1,'./SEWAM Results Scripts')
from lookup_scenarios import get_scn_name
from weap_results_v1 import read_weap_results
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import scipy.stats as stats
import calendar as cal

from matplotlib import cm
import seaborn as sns
from plot_performance import plot_climate_surface

# %matplotlib qt

pltloc = './SEWAM Results Analyses/Question 3/Part 4 - Surfaces of All Scenario Combinations/' #plot location

wr, loitab = read_weap_results(recalc=0) # read in daily performance
lois = wr['LOI'].unique() #list of LOIs
months = [cal.month_abbr[int(m)] for m in np.arange(1,13)] #all month names
wmts = [sl.replace(' ', '\n') for sl in ['Critically Dry','Dry','Below Median','Above Median','Wet','Extremely Wet']] #WMTs
for l in lois: #loop through LOIs
    #status update
    lnum = str(np.where(lois == l)[0][0] + 1)
    print('Processing LOI ' + str(int(l)) + ', ' + str(lnum) + '/' + str(len(lois)))
    loiday = wr.loc[wr['LOI']==l,:] #filter daily performance by LOI
    sscs = np.sort(loiday['SSC'].unique()) #all human scenarios
    for ssc in sscs: #loop through human scenarios
        slab = get_scn_name(ssc=[ssc])[0] #human scenario labels
        escs = np.setdiff1d(np.sort((loiday.loc[loiday['SSC'] == ssc])['ESC'].unique()),[1]) #get all ESCs except 1 (no IFT)
        if len(escs) > 0: #make sure there is data plot
            ind = loiday.groupby(['month','WMT']).sum().index #get index of month/WMT
            srfplteco = pd.DataFrame(index=ind) #eco freq
            srfplthlc = pd.DataFrame(index=ind) #local human freq
            srfplthal = pd.DataFrame(index=ind) #all CA human freq
            srfpltdef = pd.DataFrame(index=ind) #mean impairment
            srfpltdpf = pd.DataFrame(index=ind) #mean standardized impairment

            for esc in escs: #loop through ecological scenarios
                elab = get_scn_name(esc=[esc])[0] #eco scenario string
                scnday = loiday.loc[(loiday['SSC'] == ssc) & (loiday['ESC'] == esc)] #filter daily performance by scenario

                srftot = scnday.groupby(['month','WMT']).count()['Eco Met'] # total number of days
                srfmeteco = scnday.groupby(['month', 'WMT']).sum()['Eco Met'] #days IFT met
                srfplteco.loc[:, esc] = srfmeteco.loc[srfplteco.index] / srftot.loc[srfplteco.index] #eco frq
                srfmethlc = scnday.groupby(['month','WMT']).sum()['Hum Local Met'] #days local human met
                srfplthlc.loc[:, esc] = srfmethlc.loc[srfplthlc.index] / srftot.loc[srfplthlc.index] #local hum frq
                srfmethal = scnday.groupby(['month','WMT']).sum()['Hum All Met'] #days all CA human met
                srfplthal.loc[:, esc] = srfmethal.loc[srfplthal.index] / srftot.loc[srfplthal.index] #all CA hum freq

                srfpltdef.loc[:, esc] = scnday.groupby(['month','WMT']).mean()['Impairment'] #calculate mean imp
                srfpltdpf.loc[:, esc] = scnday.groupby(['month', 'WMT']).mean()['Standardized Impairment'] #calculate mean stnd imp

            for e in range(len(escs)): #loop through eco scenarios to create surface plots
                esc = escs[e]
                plot_climate_surface(srfplteco,esc,ssc, months, wmts,l, elatype=1, pltloc=pltloc)
                plot_climate_surface(srfplthal,esc,ssc, months, wmts,l,  elatype=2, pltloc=pltloc)
                plot_climate_surface(srfplthlc, esc, ssc, months, wmts,l, elatype=3, pltloc=pltloc)
                plot_climate_surface(srfpltdef, esc, ssc, months, wmts,l, elatype=4, pltloc=pltloc)
                plot_climate_surface(srfpltdpf, esc, ssc, months, wmts,l, elatype=5, pltloc=pltloc)