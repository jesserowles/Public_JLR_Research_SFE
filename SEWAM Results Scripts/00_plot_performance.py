# This script holds all functions that create plots in support of answer the 4 research questions. All
# of the data processing and math occurs in other scripts that call the functions here to format and
# create the plots.

import sys
from lookup_scenarios import get_scn_name
import pandas as pd
import calendar as cal
import  matplotlib.pyplot as plt
from weap_results_v1 import read_weap_results
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.ticker as mt
import scipy.stats as stats
from matplotlib import cm
import seaborn as sns
import matplotlib.gridspec as gs
from mpl_toolkits.mplot3d import Axes3D as a3d
from matplotlib.lines import Line2D as l2d
# %matplotlib qt

def plot_df_climate(df,mw,elatype, l, scnum, pltloc, q4loc, se=0):
    # this creates plots of Frequency of Human demands or frequency of ecological demands.
    # Inputs:
    #   df - input dataframe as processed where rows are month or WMT and columns are scenarios
    #   mw - 1 for month, 2 for WMT
    #   elatype - 1 for ecological performance, 2 for local human demands, 3 for all upstream human demands
    #   l - the LOI number as a float
    #   scnum - the human scenario that all eco scenarios are plotted for, or the eco scenario all hum scenarios
    #      are plotted for. Which is which depends on value of se.
    #   pltloc - directory where original plots are stored
    #   q4loc - directory where plots annoted with climate and scenario variability are stored
    #   se - 0 for a single eco scenario across human scenarios, 1 for a single human scenario across eco scenarios

    #process inputs
    if elatype == 1: #eco performance
        pfstr = 'Eco'
    elif elatype == 2:  # Local performance
        pfstr = 'Local'
    elif elatype == 3:  # all upstream performance
        pfstr = 'All Upstream'
    else:
        print('elatype entered incorrectly')
        sys.exit()

    if mw == 1: #month
        xlab = [cal.month_abbr[int(m)] for m in df.index]
        cstr = 'Month'
        cx = 6
    elif mw == 2: #WMT
        xlab = [sl.replace(' ', '\n') for sl in
                ['Critically Dry', 'Dry', 'Below Median', 'Above Median', 'Wet', 'Extremely Wet']]
        cstr = 'WMT'
        cx = 2.5

    if se == 0:
        legstr = get_scn_name(ssc=df.columns)
        scnlab = 'Across SSCs, ' + get_scn_name(esc=[scnum])[0]
    elif se == 1:
        legstr = get_scn_name(esc=df.columns)
        scnlab = 'Across ESCs, ' + get_scn_name(ssc=[scnum])[0]



    fig = plt.figure(figsize=[8, 6])
    #plot each scenario from rows of input dataframe as a different color line - performance on y, month/WMT on x
    ax = df.plot(style='.-',
                        title='Percent of Days '+pfstr+ ' Demand Met in Each ' +cstr + '\nLOI ' + str(int(l)) + ', ' + scnlab,
                        colormap='gist_rainbow')
    plt.xticks(ticks=df.index, labels=xlab)
    ax.yaxis.set_major_formatter(mt.PercentFormatter(1.0)) #processes y axis to be %
    ax.set_ylabel('Percent Days Met')
    ax.set_xlabel(cstr)
    lgd = plt.legend(labels=legstr, bbox_to_anchor=[1.05, 1]) # put legend outside figure bounds so no lines are covered
    ax.set_ylim([0, 1])
    #save first plot to pltloc
    plt.savefig(pltloc + 'LOI ' + str(int(l)) + ' ' + cstr + ' ' + pfstr + ' Demand Performance ' + scnlab + '.png',
                bbox_extra_artists=(lgd,), bbox_inches='tight')

    # calculate and annotate climate variability and scenario variability
    minm = df.min(axis=1) #performance of lowest performing scenario in each month or WMT
    maxm = df.max(axis=1) #performance of highest performing scenario in each month or WMT
    diffacs = maxm - minm #difference between highest and lowest performance in each month/WMT
    mxdfm = diffacs.index[diffacs == diffacs.max()][0] #month of WMT where difference is greatest
    dfs = diffacs[mxdfm] #value of scenario variability
    #plot dotted lines of lower and upper bounds of scenario variability
    plt.plot([mxdfm - 0.5, mxdfm + 0.5], [minm[mxdfm], minm[mxdfm]], 'k--')
    plt.plot([mxdfm - 0.5, mxdfm + 0.5], [maxm[mxdfm], maxm[mxdfm]], 'k--')
    #draw arrow from lower to upper bound of scenario variability
    plt.annotate(text='', xy=(mxdfm, maxm[mxdfm]), xytext=(mxdfm, minm[mxdfm]),
                 arrowprops=dict(arrowstyle='<->', color='black'))
    #set y position of label so it's not off the edge of the plot
    if maxm[mxdfm] + 0.05 > 1:
        y = minm[mxdfm] - 0.05
    else:
        y = maxm[mxdfm] + 0.05
    #annotate scenario variability
    plt.text(mxdfm, y, str(round(dfs * 100, 1)) + '%', horizontalalignment='center')
    #calculate and annotate climate variability
    mins = df.min() #performance in lowest performing month/WMT in each scenario
    maxs = df.max() #performance in highest performing month/WMT in each scenario
    if se == 0: #when looking across human scenarios, the scenario to calculate climate variability for is baseline
        mxdfs = 1
    else: #when looking across ecological scenarios, use scenario that has greatest variability among month/WMTs
        diffacm = maxs-mins #calculate difference between highest and lowest performing month/WMT
        mxdfs = diffacm.index[diffacm == diffacm.max()][0] #find scenario where difference is greatest
    dfc = maxs[mxdfs] - mins[mxdfs] #difference across climate
    #plot dashed lines from lower to upper bounds of climate variability
    plt.plot([1, 12], [mins[mxdfs], mins[mxdfs]], 'r--')
    plt.plot([1, 12], [maxs[mxdfs], maxs[mxdfs]], 'r--')
    #set y position of label so it's not off the edge of the plot
    if mins[mxdfs] - 0.1 < 0:
        y = maxs[mxdfs] + 0.1
    else:
        y = mins[mxdfs] - 0.1
    #annotate value of climate variability to plot with arrow
    plt.text(cx, y, str(round(dfc * 100, 1)) + '%',
             horizontalalignment='center', color='red')
    plt.annotate(text='', xy=(cx, maxs[mxdfs]), xytext=(cx, mins[mxdfs]),
                 arrowprops=dict(arrowstyle='<->', color='red'))
    #save plot to separate location
    plt.savefig(q4loc + 'LOI ' + str(int(l)) + ' ' + cstr + ' ' + pfstr + ' Demand Performance With Prf Diff ' + scnlab + '.png',
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

    #calculate CMRS as scenario variability divided by climate variability
    clscdiff = dfs / dfc
    return clscdiff #output value of CMRS for plotting later

def plot_prf_table(df,mw,elatype,pltloc, bstr='',xtls = [0], ytls = [0], se=0, defma = 0):
    #this function plots performance values (specifically CMRS) from a dataframe by one type of scenario and location
    #Inputs:
    #   df - input table where rows are scenario number, columns are location
    #   mw - 1 for being across Month, 2 for being across WMT
    #   elatype - 1 for ecological demands, 2 for local human demands, 3 for all upstream human demands,
    #       4 for impairment, 5 for standardized impairment
    #   pltloc - directory to save plots
    #   bstr - String for plot label. Default: ''
    #   xtls - input xticklabels. Default: column names of df
    #   ytls - input yticklabels. Default: index names of df (i.e., row names)
    #   se - 0 to label as performance across eco scenarios, 1 to label as performance across human scenarios. Default: 0
    #   defma - When using impairment or standardized impairment, the number of days the moving average was
    #       calculated for. Default: 0 (not labeled)

    if len(xtls) == 1:
        xtls = df.columns
    if len(ytls) == 1:
        ytls = df.index


    if mw == 1: #month
        cstr = 'Month'
    elif mw == 2: #WMT
        cstr = 'WMT'

    vmx = 1 #max of color scale
    if elatype == 1:  # eco performance
        pfstr = 'Eco'
    elif elatype == 2:  # Local performance
        pfstr = 'Local'
    elif elatype == 3:  # all upstream performance
        pfstr = 'All Upstream'
    elif elatype == 4:
        pfstr = 'Impairment'
    elif elatype == 5:
        pfstr = 'Standardized Impairment'


    if elatype >= 4:#specify what type of impairment or standardized impairment to be used
        if defma == 0:
            pfstr = 'Mean ' + pfstr #mean
        else:
            pfstr = 'Max ' + str(int(defma)) + '-Day MA ' + pfstr #max of moving average


    if se == 0:
        sestr = 'ESCs'
    elif se == 1:
        sestr = 'SSCs'

    df = df.astype(float)

    #plot table of performance values with jet colormap from 0 to vmx. Values are 2 digit floats as specified in fmt=".2f"
    sns.heatmap(df, cmap='jet', vmin=0, vmax=vmx,
                xticklabels = xtls,
                yticklabels = ytls,
                annot=True, fmt=".2f")
    plt.title('Climate/Management Relative Sensitivity\nBy ' +cstr+ ' and across ' + sestr +
              ' in ' + pfstr + ' Performance')
    #save using strings set by input values in directory specified
    plt.savefig(pltloc + bstr + ' ' + cstr + ' ' + pfstr + '.png', bbox_inches="tight")
    plt.close()

def process_and_plot_table(timedf, mdescloc, mnescloc, mdsscloc, mnsscloc, m, l, pltloc, elatype, mw, defma = 0):
    # this function plots performance tables and adds the maximum difference across each type of scenarios
    # Inputs:
    #   timedf - dataframe input of performance where rows are eco scenarios, columns are human scenarios.
    #   mdescloc - dataframe of maximum difference across eco scenarios for all locations. This table is
    #       appended with the max diff values calculated for the current location
    #   mnescloc - dataframe of mean of all eco scenarios for all locations. This table is
    #       appended with the mean values calculated for the current location
    #   mdsscloc - dataframe of maximum difference across human scenarios for all locations. This table is
    #       appended with the max diff values calculated for the current location
    #   mnescloc - dataframe of mean of all human scenarios for all locations. This table is
    #       appended with the mean values calculated for the current location
    #   m - month or WMT number as an int or float
    #   l - LOI number as a float
    #   mw - 1 for being across Month, 2 for being across WMT, 3 for the entire POR
    #   elatype - 1 for ecological demands, 2 for local human demands, 3 for all upstream human demands,
    #       4 for impairment, 5 for standardized impairment
    #   defma - When using impairment or standardized impairment, the number of days the moving average was
    #       calculated for. Default: 0 (not labeled)

    vmx = 1
    fmt = '.1%' #default format is one decimal place and a percent
    if elatype == 1:
        tstr = 'IFT'
        fstr = 'Eco Demands'
    elif elatype == 2:
        tstr = 'Local Human Demands'
        fstr = 'Local Human Demands'
    elif elatype == 3:
        tstr = 'All Upstream Human Demands'
        fstr = 'All Human Demands'
    elif elatype == 4: # impairment
        tstr = 'Impairment'
        fstr = 'Imp'
        fmt = '.2g' #change format to 2 decimal place float since this metric is not a %
    elif elatype == 5:  # standardized impairment
        tstr = 'Standardized Impairment'
        fstr = 'Stnd Imp'

    if elatype >= 4:
        vmx = max(timedf.max())
        if defma == 0: #mean imp or standardized imp
            fstr = 'Mean ' + fstr
            tstr = 'Mean ' + tstr
        else: #max of moving average imp or standardized imp
            fstr = str(int(defma)) + '-Day MA ' + fstr
            tstr = str(int(defma)) + '-Day MA ' + tstr

    if mw == 1: # calendar month
        tmwstr = cal.month_name[m]
        fmwstr = 'Month ' + str(int(m)) + ' (' + tmwstr + ')'
        ms = me = m
    elif mw == 2: # WMT
        wmtnam = ['Critically Dry', 'Dry', 'Below Median', 'Above Median', 'Wet', 'Extremely Wet']
        tmwstr = wmtnam[int(m) - 1]
        fmwstr = 'WMT ' + str(int(m)) + ' (' + tmwstr + ')'
        ms = me = m
    elif mw == 3: #all
        tmwstr = 'All Days'
        fmwstr = tmwstr
        ms = mdsscloc.index
        me = mdescloc.index

    if (elatype >= 1) & (elatype <= 3):
        fulltitle = 'Percent Days ' + tstr + ' Met'
    else:
        fulltitle = tstr


    timedf = timedf.astype(float)

    #get names of scenarios for labels
    ssclab = get_scn_name(ssc=timedf.columns)
    esclab = get_scn_name(esc=timedf.index)
    #calculate max diff across ecological and human scenario (row and column)
    mxdfesc = timedf.max() - timedf.min()
    timedf['Max Diff'] = timedf.max(axis=1) - timedf.min(axis=1)
    timedf.loc['Max Diff', :] = mxdfesc
    #add max diff to dataframe in the column for this location
    mdescloc.loc[me, l] = timedf.loc[mdescloc.loc[me, l].index, 'Max Diff'].get_values()
    mdsscloc.loc[ms, l] = mxdfesc.get_values()
    #add mean to dataframe in the column for this location
    mnescloc.loc[me, l] = timedf.loc[mnescloc.loc[me, l].index, ~timedf.columns.isin(['Max Diff'])].mean(
        axis=1).get_values()
    mnsscloc.loc[ms, l] = timedf.loc[
        ~timedf.index.isin(['Max Diff']), mnsscloc.loc[ms, l].index].mean().get_values()

    #create table to include the max diff values calculated.
    fig = plt.figure(figsize=[9, 6])
    sns.heatmap(timedf, cmap='jet', vmin=0, vmax=vmx,
                xticklabels=np.append(ssclab, 'Max Diff'),
                yticklabels=np.append(esclab, 'Max Diff'),
                annot=True, fmt=fmt)
    plt.title(fulltitle + ', LOI ' + str(int(l)) + ' - ' + tmwstr)
    #save fig to pltloc
    plt.savefig(pltloc + 'LOI ' + str(int(l)) + ' ' + fstr+ ' in ' +fmwstr+
                ' All Scenarios.png', bbox_inches="tight")
    plt.close()
    return mdescloc, mnescloc, mdsscloc, mnsscloc #return these values so new locations can be added

def plot_md_mn_table(df,xts,yts,elatype, es, mw, i, nd, pltloc, defma = 0):
    # this script plots the max diff or mean across scenarios as calculated in process_and_plot_table.
    # Inputs:
    #   df - dataframe input of performance where rows are scenarios, columns are LOIs
    #   xts - input xticklabels
    #   yts - input yticklabels
    #   elatype - 1 for ecological demands, 2 for local human demands, 3 for all upstream human demands,
    #       4 for impairment, 5 for standardized impairment
    #   es - indicator of whether performance is shown across ESCs (es = 1) or SSCs (es = 2)
    #   mw - 1 for being across Month, 2 for being across WMT, 3 for the entire POR
    #   i - index associated with which row of df to plot - represents a month when mw = 1, WMT when mw = 2,
    #       or all when mw = 3 (i=0 in this case)
    #   nd - indicator of whether mean (nd = 1) or max difference across scenarios (nd = 2)
    #   pltloc - location to save plots
    #   defma - When using impairment or standardized impairment (elatype = 4 or 5), the number of days the moving
    #       average was calculated for. Default: 0 (not labeled)

    df = df.astype(float) #convert df to float so statistics can be run on it
    vmx = 1 #max of color scale
    fmt = '.1%' #default number format is a percent with one decimal place
    if elatype == 1: #frequency of ecological demands
        tstr = 'Eco'
        fstr = 'Eco'
    elif elatype == 2: #frequency of local subwatershed human demands
        tstr = 'Local Human Demand'
        fstr = 'Local Human'
    elif elatype == 3: #frequency of all contributing area human demands
        tstr = 'All Upstream Human Demand'
        fstr = 'All Human'
    elif elatype == 4: #impairment
        tstr = 'Impairment'
        fstr = 'Imp'
        fmt = '.2g'
        vmx = max(df.max()) #change colorscale since values are no longer percent
    elif elatype == 5: #standardized impairment
        tstr = 'Standardized Impairment'
        fstr = 'Stnd Imp'


    if elatype >= 4:
        if defma == 0: #no moving average defined, so label it as 'mean'
            fstr = 'Mean ' + fstr
            tstr = 'Mean ' + tstr
        else: #use moving average input to label plots
            fstr = str(int(defma)) + '-Day MA ' + fstr
            tstr = str(int(defma)) + '-Day MA ' + tstr

    if mw == 1: # calendar month
        tmwstr = cal.month_name[i]
        fmwstr = 'Month ' + str(int(i)) + ' (' + tmwstr + ')'
    elif mw == 2: # WMT
        wmtnam = ['Critically Dry', 'Dry', 'Below Median', 'Above Median', 'Wet', 'Extremely Wet']
        tmwstr = wmtnam[int(i) - 1]
        fmwstr = 'WMT ' + str(int(i)) + ' (' + tmwstr + ')'
    elif mw == 3: #all
        tmwstr = 'All Days, All Scenarios'
        fmwstr = tmwstr
        i = df.index

    if es == 1: #across ecological scenarios (ESCs)
        estr = 'ESCs'
    elif es == 2: #across human scenarios (SSCs)
        estr = 'SSCs'

    if nd == 1: #mean
        ndstr = 'Mean'
    elif nd == 2: #max diff
        ndstr = 'Max Diff'

    fig = plt.figure(figsize=[9, 6])
    #create table of values using jet colormap and input x and y tick labels
    sns.heatmap(df.loc[i, :], cmap='jet', vmin=0, vmax=vmx,
                xticklabels=xts,
                yticklabels=yts,
                annot=True, fmt=fmt)
    plt.title(ndstr + ' in ' + tstr + ' Performance Across ' + estr + ' for ' + tmwstr)
    plt.savefig(pltloc + 'All LOIs ' + ndstr + ' Across ' + estr + ' ' + fstr +
                ' in ' + fmwstr + '.png', bbox_inches="tight")
    plt.close()

def plot_def(df, mw, dp, l, se, scnlab, pltloc, q4loc, defma = 0):
    # This function plots impairment or standardized impairment against month or WMT for all human or eco scenarios
    # Inputs:
    #   df - dataframe input of performance where rows are months or WMTs, columns are scenarios.
    #   mw - 1 for being across Month, 2 for being across WMT, 3 for the entire POR
    #   dp - 1 for impairment, 2 for standardized impairment
    #   l - LOI number as a float
    #   se - 1 when the plot shows an ecological scenario across human scenarios, 2 is a human scenario across eco scenarios
    #   scnlab - string associated with the single ecological scenario being plotted for se = 1, or the human scenario for se = 2
    #   pltloc - directory where original plots are stored
    #   q4loc - directory where plots annoted with climate and scenario variability are stored
    #   defma - When using impairment or standardized impairment, the number of days the moving average was
    #       calculated for. Default: 0 (not labeled, mean is plotted)


    if mw == 1: #month
        xlb = [cal.month_abbr[int(m)] for m in df.index] #get a list of abberviated month names
        fmwstr = 'Month'
        cx = 6 #x location of where climate variability is annotated on plot. for month, this value is plotted in June.
    elif mw == 2:
        xlb = [sl.replace(' ', '\n') for sl in
                    ['Critically Dry', 'Dry', 'Below Median', 'Above Median', 'Wet', 'Extremely Wet']] #get list of WMTs
        fmwstr = 'WMT'
        cx = 2.5 #x location of where climate variability is annotated on plot. for WMT, this value is plotted between BM and AM.

    if dp == 1: #impairment
        tstr = 'Impairment'
        fstr = 'Imp'
    elif dp == 2: #standardized impairment
        tstr = 'Standardized Impairment'
        fstr = 'Stnd Imp'

    if defma == 0: #no moving average value input, use mean
        fstr = 'Mean ' + fstr
        tstr = 'Mean ' + tstr
    else:
        fstr = 'Max ' + str(int(defma)) + '-Day MA ' + fstr
        tstr = 'Max ' + str(int(defma)) + '-Day MA ' + tstr

    if se == 1: #label as single ecological scenario across human scenarios
        lgdlbl = get_scn_name(ssc=df.columns)
        scnlab = 'Across SSCs, ' + scnlab
    elif se == 2: #label as single human scenario across ecological scenarios
        lgdlbl = get_scn_name(esc=df.columns)
        scnlab = 'Across ESCs, ' + scnlab


    fig = plt.figure(figsize=[8, 6])
    ax = df.plot(style='.-',
                        title= tstr +'\nLOI ' + str(
                            int(l)) + ', ' + scnlab,
                        colormap='gist_rainbow')
    plt.xticks(ticks=df.index, labels=xlb) #set xstick marks and label
    if dp == 2: #only format y-axis as percent if standardized impairment is plotted
        ax.yaxis.set_major_formatter(mt.PercentFormatter(1.0))
    ax.set_ylabel(tstr)
    ax.set_xlabel(fmwstr)
    lgd = plt.legend(labels=lgdlbl, bbox_to_anchor=[1.05, 1]) #plot legend outisde axis bounds so it doesn't cover lines

    plt.savefig(pltloc + 'LOI ' + str(int(l)) + ' ' + fstr + ' by ' + fmwstr
                + ' - ' + scnlab + '.png',
                bbox_extra_artists=(lgd,), bbox_inches='tight')

    # annotate climate and scenario variability on plot
    minm = df.min(axis=1) # lowest value in each month or WMT
    maxm = df.max(axis=1) # highest value in each month or WMT
    diffacs = maxm - minm #difference between highest and lowest value in each month/WMT
    ydel = diffacs.max()*0.02 #this variable sets the y offset from the calculated value to annotate the plot
    mxdfm = diffacs.index[diffacs == diffacs.max()][0] # get index when difference is largest
    if dp == 1: #deficit
        dfs = maxm[mxdfm] - minm[mxdfm] #scenario variability value
        rd = 2
        pstr = ''
    else: #standardized deficit
        dfs = (maxm[mxdfm] - minm[mxdfm]) * 100 #scenario variability value
        rd = 2
        pstr = '%' #format as percent
    #plot boundaries of and annotate value of scenario variability
    plt.plot([mxdfm - 0.5, mxdfm + 0.5], [minm[mxdfm], minm[mxdfm]], 'k--')
    plt.plot([mxdfm - 0.5, mxdfm + 0.5], [maxm[mxdfm], maxm[mxdfm]], 'k--')
    plt.annotate(text='', xy=(mxdfm, maxm[mxdfm]), xytext=(mxdfm, minm[mxdfm]),
                 arrowprops=dict(arrowstyle='<->', color='black'))
    if maxm[mxdfm] + ydel > 1: #if y value of annotation is outside plot bounds, drop it to below the line rather than above
        y = minm[mxdfm] - ydel
    else:
        y = maxm[mxdfm] + ydel
    plt.text(mxdfm, y, str(round(dfs, rd)) + pstr, horizontalalignment='center')
    mins = df.min() #lowest month or WMT in each scenario
    maxs = df.max() #highest month or WMT in each scenario
    diffacm = maxs-mins #difference between highest and lowest in each scenario
    if se == 1:
        mxdfs = 1 #when looking across human scenarios, use baseline scenario to determine climate variability
    else:
        mxdfs = diffacm.index[diffacm == diffacm.max()][0] #when looking across eco scenarios, use eco scenario of greatest climate variability

    if dp == 1:
        dfc = maxs[mxdfs] - mins[mxdfs] #calculate climate variability
    else:
        dfc = (maxs[mxdfs] - mins[mxdfs] ) * 100 #calculate climate variability as a percent
    #draw lines to mark climate variability
    plt.plot([1, 12], [mins[mxdfs], mins[mxdfs]], 'r--')
    plt.plot([1, 12], [maxs[mxdfs], maxs[mxdfs]], 'r--')
    if mins[mxdfs] - (ydel * 2) < 0:
        y = maxs[mxdfs] + (ydel * 2)
    else:
        y = mins[mxdfs] - (ydel * 2)
    plt.text(cx, y, str(round(dfc, rd)) + pstr,
             horizontalalignment='center', color='red')
    plt.annotate(text='', xy=(cx, maxs[mxdfs]), xytext=(cx, mins[mxdfs]),
                 arrowprops=dict(arrowstyle='<->', color='red'))
    plt.savefig(q4loc + 'LOI ' + str(int(l)) + ' ' + fmwstr + ' ' + fstr + ' Performance With Prf Diff ' + scnlab + '.png',
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

    clscdiff = dfs / dfc #calculate CMRS
    return clscdiff

def plot_change_from_baseline(jpdf,escnum, metric, mtrloc):
    #this fucntion creates bar and violin plots of relative performance of human scenario
    # Inputs:
    #   jpdf - dataframe of relative performance values where rows are human scenarios and columns are locations
    #   escnum - number associated with ecological scenario being plotted against (or 0 if average across
    #       eco sceanrios to be used)
    #   metric - performance metric name to be used in labelling plot
    #   mtrloc - the location to save the plots, should be in folder named based on metric in 'Question 1' folder

    lmn = jpdf.mean(axis=1) #calculate mean of all locations relative performance to plot as bar size
    allssc = lmn.index #human scenarios that come from the index
    ssclst = list(get_scn_name(ssc=allssc)) # make list of human sceanrio names
    ssclab = [sl.replace(' ', '\n') for sl in ssclst] # replace spaces in human scenario names with new line characters for readability on plot

    if escnum == 0: #average across ecological scenarios
        esclab = ['All Ecological Scenarios']
    else: # individual ecological scenarios
        esclab = get_scn_name(esc=[escnum])


    #bar plots of average relative performance across locations
    fig = plt.figure(figsize=[8, 6])
    ax = fig.add_subplot(1, 1, 1)
    plt.bar(x=lmn.index, height=lmn)
    ax.yaxis.set_major_formatter(mt.PercentFormatter(1.0)) #format y axis as percent
    plt.xticks(ticks=lmn.index, labels=ssclab)
    ax.set_title(metric + '\nRelative Performance from Baseline in ' + esclab[0])
    ax.set_ylabel('Change from Baseline')
    ax.set_xlabel('Sensitivity Scenario')
    plt.savefig(mtrloc + 'Bars Change From Baseline ' + metric + ' ' + esclab[0] + '.png')
    plt.close()

    #violin plots of all locations
    fig = plt.figure()
    ax = fig.gca()
    sns.violinplot(data=jpdf.T, scale='width')
    ax.autoscale(False)
    ax.plot([-1,10],[0,0],'k--',alpha=0.5) #draw dashed line at zero
    ax.yaxis.set_major_formatter(mt.PercentFormatter(1.0))
    ax.set_xticklabels(ssclab)
    plt.ylabel('Percent Change from Baseline')
    ax.set_title(metric + '\nRelative Performance from Baseline Distributions\n' + esclab[0])
    plt.tight_layout() #have to do this to get text in figure window
    plt.savefig(mtrloc + 'Violins Change From Baseline ' + metric + ' ' + esclab[0] + '.png')
    plt.close()

def plot_change_from_bl_numrsp(jpdf, escnum, r, rsptab, metric, mtrloc):
    #this function plots relative performance against numeric RSPs with linear trendline
    # Inputs:
    #   jpdf - dataframe of relative performance values where rows are human scenarios and columns are locations
    #   escnum - number associated with ecological scenario being plotted against (or 16 if average across
    #       eco sceanrios to be used)
    #   r - RSP as text - should match index of jpdf
    #   rsptab - table of RSPs by location
    #   metric - performance metric name to be used in labelling plot
    #   mtrloc - the location to save the plots, should be in folder named based on metric in 'Question 1' folder

    if escnum <= 15:
        esclab = get_scn_name(esc=[escnum])
    else: #average across all ecological scenarios
        esclab = ['All Eco Scenario Mean']
    ycols = list(jpdf.columns.astype(str))
    jpdf.loc[:, r] = rsptab.loc[jpdf.index, r] #get RSPs from RSP table
    jpdf.columns = jpdf.columns.astype(str) #convert column names to string
    jpdf.loc[jpdf[r] == -1, r] = np.nan #make sure any RSPs of value -1 are not plotted
    if len(jpdf[r]) > 1:
        fmx = jpdf[r].sort_values(ascending=False).iloc[0] #RSP of greatest value
        smx = jpdf[r].sort_values(ascending=False).iloc[1] #RSP of second greatest value
        if fmx/smx > 3: #if the greatest RSP value is 3 times greater than the second, don't plot it (remove outliers)
            jpdf.loc[jpdf[r]==fmx,r] = np.nan
        jpdf = jpdf.sort_values(by=r).astype(float).dropna() #remove na

    leglab = get_scn_name(ssc=[float(y) for y in ycols]) #list of human scenarios for legend labels
    colors = cm.gist_rainbow(np.floor(np.linspace(0,255,len(ycols)+1)).astype(int)[1:len(ycols)+1]) #get list of colors for plotting
    ax = jpdf.plot(x=r, y=ycols, marker='.',markersize=7,ls='none',color=colors, figsize=(8,6)) #plots points for each

    #calculate linear fit for each human scenario and plot
    pfit = jpdf.apply(lambda x: np.polyfit(jpdf.loc[:, r], x, 1), result_type='expand')
    newx = np.linspace(jpdf[r].min(),jpdf[r].max(),100)
    pval = pfit.apply(lambda x: np.polyval(x,newx),result_type='expand')
    pval.plot(x=r,y=ycols,ax=ax,color=colors,linewidth=3)
    ax.autoscale(tight=False)
    ax.autoscale(False)
    xbd = ax.get_xbound()
    ax.plot(xbd,[0,0],'k--',alpha=0.5) #plot zero line
    ax.margins(x=0.1,y=0.1)
    ax.yaxis.set_major_formatter(mt.PercentFormatter(1.0))
    hd = [l2d([],[],color=colors[i],marker='.',label=leglab[i]) for i in range(len(colors))]
    lgd = plt.legend(handles=hd, bbox_to_anchor=[1.05, 1], loc='upper left')
    plt.title('Change from Baseline Scenario in\n' + metric + '\n' + esclab[0])
    plt.ylabel('Change in Performance')
    plt.tight_layout()
    plt.savefig(mtrloc+'Performance in ESC '+str(int(escnum))+', '+esclab[0] + ' by RSP ' + r + ' .png',
                bbox_extra_artists=(lgd,), bbox_inches='tight')

    plt.close()


def plot_change_from_bl_catrsp(jpdfin, escnum, catrsp, rsptab, metric, mtrloc):
    #this function generates violin plots of relative performance against categorical RSPs
    # Inputs:
    #   jpdfin - dataframe of relative performance values where rows are human scenarios and columns are locations
    #   escnum - number associated with ecological scenario being plotted against (or 16 if average across
    #       eco sceanrios to be used)
    #   catrsp - list of all categorical RSP names
    #   rsptab - table of RSPs by location
    #   metric - performance metric name to be used in labelling plot
    #   mtrloc - the location to save the plots, should be in folder named based on metric in 'Question 1' folder

    if escnum <= 15:
        esclab = get_scn_name(esc=[escnum])
    else:
        esclab = ['All Eco Scenario Mean']

    for r in catrsp: #create set of violin plots for every categorical RSP
        jpdf = jpdfin.copy().astype(float).dropna() #change data type and remove NA values
        jpdf.columns = get_scn_name(ssc=jpdf.columns) #rename columns from number to scenario names
        jcols = jpdf.columns #save off original columns
        jpdf.loc[:, r] = rsptab.loc[jpdf.index, r] #add column for RSP
        if r == 'UDP':
            jpdf[r] = jpdf[r].astype(str).str[0] #convert UDP to string

        fig = plt.figure(figsize=(10,8))
        gs1 = gs.GridSpec(3,3) #break into grid, one for each human scenario
        ax = [fig.add_subplot(ss) for ss in gs1]
        ys = [0,0] #ys tracks the highest max and lowest min of y values for each chart so all can be put on the same scale
        for s in range(len(jcols)): #need to loop through and create a plot for each human sceanrio
            jc = jcols[s] #loop thru human scenarios and put in grids
            if (r == 'UDD') & (np.isin(2230,jpdf.index)):
                pltdf = jpdf.copy().drop(2230) #2220 and 2230 are basically the same location and it breaks UDD plotting, so drop one
            else:
                pltdf = jpdf.copy()
            sns.violinplot(x=r, y=jc, data=pltdf, scale = 'width', ax=ax[s]) #create violin plots for each category and human scenario
            ax[s].yaxis.set_major_formatter(mt.PercentFormatter(1.0))
            ay = ax[s].get_ybound() #get y bounds
            ys = [min(ys[0],ay[0]), max(ys[1], ay[1])] #check if lowest and highest y value are greater than current ys values
            ax[s].autoscale(False)
            xbd = ax[s].get_xbound()
            ax[s].plot(xbd, [0, 0], 'k--', alpha=0.5) #plot dashed black line at 0

        for s in range(len(ax)): #go through and set all grids to be min y to max y
            ax[s].set_ylim(ys)
        gs1.tight_layout(fig,rect=[0,0.03,1,0.95]) #had to do this because labels kept getting cut off
        fig.suptitle('Distributions of Change in Performance from Baseline\n' +
                     metric + ' vs ' + r + ' in ' + esclab[0]) #overall figure title
        plt.savefig(mtrloc + 'Performance in ESC ' + str(int(escnum)) + ', ' + esclab[0] + ' by RSP ' + r + ' .png')
        plt.close()

def plot_climate_surface(df, esc, ssc, months, wmts,l, elatype, pltloc):
    # plots performance against month and WMT as a surface
    # Inputs:
    #   df - dataframe with performance by 2-level month/WMT index (can be generated using df.groupby(['month','WMT']) )
    #   esc - ecological scenario number of associated performance
    #   ssc - ecological scenario number of associated performance
    #   months - list of strings of month names to label plot (abbreviated names used)
    #   wmts - list of strings of WMT names to label plot (new line character instead of spaces
    #   l - LOI number
    #   elatype - 1 for ecological demands, 2 for local human demands, 3 for all upstream human demands,
    #       4 for impairment, 5 for standardized impairment
    #   pltloc - location to save folders (Usually question 3, part 4)

    if elatype == 1:
        zstr = 'Percent Days Eco Demands Met'
        fstr = 'Eco'
    elif elatype == 2:
        zstr = 'Percent Days Local Human Demands Met'
        fstr = 'Local Human'
    elif elatype == 3:
        zstr = 'Percent Days All Upstream Human Demands Met'
        fstr = 'All Human'
    elif elatype == 4:
        zstr = 'Impairment (cfs)'
        fstr = 'Imp'
    elif elatype == 5:
        zstr = 'Standardized Impairment'
        fstr = 'Stnd Imp'

    df = df.reset_index() #add columns for month and WMT, reset index to chronological number starting at 0

    fig = plt.figure(figsize=[8,6])
    ax = a3d(fig=fig)
    leg = []
    mntgrd, wmtgrd = np.meshgrid(df['month'].unique(), df['WMT'].unique()) #create two variables of gridded month/WMT values for surface
    elab = get_scn_name(esc=[esc])[0] #get eco scenario name
    slab = get_scn_name(ssc=[ssc])[0] #get human scenario name
    prfgrd = np.reshape(df[esc].get_values(),
                        (len(df['month'].unique()), len(df['WMT'].unique()))).T #reshape performance into grid variable

    # plot surfaces for each scenario
    cols = cm.jet(prfgrd / np.amax(prfgrd)) #colors of faces
    ax.plot_surface(mntgrd, wmtgrd, prfgrd, alpha=0.8, facecolors=cols)  #plot surface with 0.8 alpha (slightly transparent)

    #use input month and WMT lists to label axes
    ax.set_xlabel('Month')
    plt.xticks(ticks=df['month'].unique(), labels=months)
    ax.set_ylabel('Water Month Type')
    plt.yticks(ticks=df['WMT'].unique(), labels=wmts)
    ax.set_zlabel(zstr)
    if elatype != 4:
        ax.zaxis.set_major_formatter(mt.PercentFormatter(1.0)) #format axes as percent for everything except impairment
    if elatype <= 3: #for frequency reliability metrics, set z axes from 0 to 1 so can be visually compared easily
        ax.set_zlim([0, 1])
    plt.title('Performance for LOI ' + str(int(l)) + ', ' + elab + '/ ' + slab)
    # make space for labels
    ax.yaxis.labelpad = 20
    ax.dist=10
    plt.savefig(pltloc + 'LOI ' + str(int(l)) + ' ' + fstr + ' By Month & WMT, ' +
                slab + '-' + elab + '.png', bbox_inches='tight')
    plt.close()
