#this script reads in and processes full set of daily WEAP results and calculates performance metrics (451 in total).
# v1 is for reading in Sept 2020 model run.

import os
import pandas as pd
import numpy as np
import datetime as dt
import calendar as cal
import sys
sys.path.insert(1,'./SEWAM Results Scripts')
from lookup_scenarios import get_scn_nums

def read_weap_results(recalc=0, resave=0, ltonly = 0):
    # Inputs:
    #   recalc - Indicator to determine whether results should be recalculated.
    #       recalc = 0 will simply read in the saved file denoted in ltfile and/or wrfile
    #       recalc = 1 will read in daily performance directly from model and recalculate all performance metrics
    #   resave - Indicator to determine whether results should be saved or not
    #       resave = 0 will not save to new file (saves time, good for testing)
    #       resave = 1 will save results to files listed
    #   ltonly - Indicator to determine whether daily performance needs to be loaded/calculated or not
    #       ltonly = 0 will return both the daily performance and LOI performance table
    #       ltonly = 1 will only give LOI performance table
    start = dt.datetime.now()#get time of start, used to track how long this takes
    print('Start: ', start.strftime(format='%I:%M:%S %p'))# print start time

    # specify filenames of LOI performance table (ltfile) and daily performance file (wrfile)
    ltfile = 'Reference Files/Performance by LOI Sept 2020.csv'
    wrfile = 'Reference Files/Daily Performance Sept 2020.csv'

    # tell user what files are being loaded
    print('LOI table read from '+ltfile)
    print('Daily performance table read from ' + wrfile)
    if (recalc == 1): #run through and recalculate everything
        #read data from csv
        print('Recalculating all performance values. Reading in WEAP Performance...')
        ogdir = os.getcwd() #get current directory so we can switch back after getting results
        os.chdir('./Reference Files')
        lperr = pd.read_excel('WEAP LP Errors 09_30_2020.xlsx',header=3) #read in sheet that has scenarios and errors from WEAP
        wr_raw = pd.read_csv('SFER_Complete_Results_File Sept 2020.csv') #read in complete daily results from WEAP
        wr = wr_raw.dropna() #remove columns with na's
        print('WEAP Performance table read, converting dates to Timestamps...')
        wr.index = pd.to_datetime(wr['Date'],format=' %m/%d/%Y') #set index of df to be dates, format accordingly
        wr['Date'] = wr.index
        print('Timestamps converted, processing daily performance...')
        wr.loc[:,'month'] = wr.index.month #save off month
        wr.loc[:, 'water year'] = wr.index.year #save water year
        wr.loc[wr['month'] >= 10, 'water year'] = wr.loc[wr['month'] >= 10, 'water year'] + 1
        wr.loc[wr.loc[:,'Sensitivity_Scenario_Code'] == '10','Sensitivity_Scenario_Code'] = 10 #fix weird formatting

        #fix rounding errors in WEAP Outputs (should only affect eWRIMS storage off scenarios)
        wr.loc[(abs(wr['DT_Supplied_eWRIMS_CFS'] - wr['DT_Demand_e_CFS']) < 0.001) &
               (wr['DT_Supplied_eWRIMS_CFS'] > 0),'DT_Supplied_eWRIMS_CFS'] = \
            wr.loc[(abs(wr['DT_Supplied_eWRIMS_CFS'] - wr['DT_Demand_e_CFS']) < 0.001) &
                   (wr['DT_Supplied_eWRIMS_CFS'] > 0), 'DT_Demand_e_CFS']

        wr.loc[(abs(wr['DT_Supplied_eWRIMS_Local_CFS'] - wr['DT_Demand_e_Local_CFS']) < 0.001) &
               (wr['DT_Supplied_eWRIMS_Local_CFS'] > 0),'DT_Supplied_eWRIMS_Local_CFS'] = \
            wr.loc[(abs(wr['DT_Supplied_eWRIMS_Local_CFS'] - wr['DT_Demand_e_Local_CFS']) < 0.001) &
                   (wr['DT_Supplied_eWRIMS_Local_CFS'] > 0), 'DT_Demand_e_Local_CFS']

        #interpolating LP error days. This takes the scenarios and date with errors and saves them off.
        print('Interpolating flow for days with LP errors...')
        for err in lperr.index: #loop through dates in error sheet, format dates and scenarios
            ssc, esc = get_scn_nums(lperr.loc[err,'Scenario']) #get affected scenario based on text
            mn = lperr.loc[err,'Day'].month
            dy = lperr.loc[err,'Day'].day
            yr = lperr.loc[err,'Year']
            if mn >= 10: #water year is provided
                yr = yr + 1
            lperr.loc[err,'newdate'] = pd.Timestamp(year=yr,month=mn,day=dy) #create timestamp
            lperr.loc[err,'ssc'] = ssc #human scenario affected
            lperr.loc[err,'esc'] = esc #ecological scenario affected

        #Here, the streamflow in the dates and scenarios with errors are set to nan's, then interpolated between.
        wr.loc[wr[['Date', 'Sensitivity_Scenario_Code', 'EPP_Scenario_Code']].apply(tuple, axis=1).isin(
            lperr[['newdate', 'ssc', 'esc']].apply(tuple, axis=1)),'Streamflow_CFS'] = np.nan
        wr['Streamflow_CFS'] = wr['Streamflow_CFS'].interpolate()

        #Round flow columns to 3 decimal places since it was determined flows below this are negligent.
        print('Rounding columns in cfs to 3 decimal places...')
        rdcol = ['Streamflow_CFS', 'DT_Demand_C_CFS',
                 'DT_Supplied_Cannabis_CFS', 'DT_Demand_e_CFS', 'DT_Supplied_eWRIMS_CFS',
                 'Instream_Flow_Target_CFS', 'EP_Target', 'EP_Achieved', 'EP_Max',
                 'DT_Demand_C_Local_CFS', 'DT_Supplied_Cannabis_Local_CFS',
                 'DT_Demand_e_Local_CFS', 'DT_Supplied_eWRIMS_Local_CFS']
        for r in rdcol:
            wr.loc[:,r] = wr.loc[:,r].astype(float).round(3)

        os.chdir(ogdir) #reset original directory

        #calculate  daily values of performance for eco demands, local subwatershed human demands, and all
        # contributing area human demands
        #volumetric by day = supply/demand
        wr.loc[:,'Vol Eco'] = np.min(np.array([np.array(wr['Streamflow_CFS']/wr['Instream_Flow_Target_CFS']),
                                               np.ones(len(wr.index))]).T,
                                     axis=1)
        wr.loc[:,'Vol Hum Local'] = np.min(np.array([np.array(wr['DT_Supplied_eWRIMS_Local_CFS']/wr['DT_Demand_e_Local_CFS']),
                                                     np.ones(len(wr.index))]).T,
                                           axis=1)

        wr.loc[:,'Vol Hum All'] = np.min(np.array([np.array(wr['DT_Supplied_eWRIMS_CFS']/wr['DT_Demand_e_CFS']),
                                                   np.ones(len(wr.index))]).T,
                                         axis=1)

        #Determine days where demands are met including 100%, 90%, 75%, and 50% of demands
        wr['Eco Met'] = wr['Streamflow_CFS'] >= wr['Instream_Flow_Target_CFS']
        wr.loc[:,'Eco Met 90%'] = wr['Streamflow_CFS'] >= (wr['Instream_Flow_Target_CFS'] * 0.9)
        wr.loc[:,'Eco Met 75%'] = wr['Streamflow_CFS'] >= (wr['Instream_Flow_Target_CFS'] * 0.75)
        wr.loc[:,'Eco Met 50%'] = wr['Streamflow_CFS'] >= (wr['Instream_Flow_Target_CFS'] * 0.5)

        wr.loc[:,'Hum Local Met'] = wr['DT_Supplied_eWRIMS_Local_CFS'] >= wr['DT_Demand_e_Local_CFS']
        wr.loc[:,'Hum Local Met 90%'] = wr['DT_Supplied_eWRIMS_Local_CFS'] >= (wr['DT_Demand_e_Local_CFS']* 0.9)
        wr.loc[:,'Hum Local Met 75%'] = wr['DT_Supplied_eWRIMS_Local_CFS'] >= (wr['DT_Demand_e_Local_CFS']* 0.75)
        wr.loc[:,'Hum Local Met 50%'] = wr['DT_Supplied_eWRIMS_Local_CFS'] >= (wr['DT_Demand_e_Local_CFS']* 0.5)

        wr.loc[:,'Hum All Met'] = wr['DT_Supplied_eWRIMS_CFS'] >= wr['DT_Demand_e_CFS']
        wr.loc[:,'Hum All Met 90%'] = wr['DT_Supplied_eWRIMS_CFS'] >= (wr['DT_Demand_e_CFS'] * 0.9)
        wr.loc[:,'Hum All Met 75%'] = wr['DT_Supplied_eWRIMS_CFS'] >= (wr['DT_Demand_e_CFS'] * 0.75)
        wr.loc[:,'Hum All Met 50%'] = wr['DT_Supplied_eWRIMS_CFS'] >= (wr['DT_Demand_e_CFS'] * 0.5)

        wr['limflow'] = wr[['Streamflow_CFS', 'Instream_Flow_Target_CFS']].min(axis=1)
        wr['limlcdm'] = wr[['DT_Supplied_eWRIMS_Local_CFS', 'DT_Demand_e_Local_CFS']].min(axis=1)
        wr['limaldm'] = wr[['DT_Supplied_eWRIMS_CFS', 'DT_Demand_e_CFS']].min(axis=1)

        #initialize columns containing impairment and standardized impairment
        wr.loc[:,'Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '3 Day Moving Avg Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '5 Day Moving Avg Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '7 Day Moving Avg Impairment'] = np.zeros_like(wr['Streamflow_CFS'])

        wr.loc[:,'Standardized Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '3 Day Moving Avg Standardized Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '5 Day Moving Avg Standardized Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        wr.loc[:, '7 Day Moving Avg Standardized Impairment'] = np.zeros_like(wr['Streamflow_CFS'])
        #single value metrics, see RSP Metric List.xlsx
        loitab = pd.DataFrame(columns=['LOI','SSC','ESC']) #columns for LOI, sensitivity scenario code (SSC), and for Ecological Demandslogical scenario code (ESC)
        i=0
        lois = wr.loc[:,'LOI'].unique()
        lenlois = len(lois)
        for l in lois: #loop through all LOIs
            loinum = np.where(lois == l)[0][0]
            print('Processing LOI ' + str(l) + ', number ' +str(loinum+1) + '/' + str(lenlois)) #print status of processing
            wrl = wr['LOI'] == l #get index of daily time series for LOI specific
            loidf = wr.loc[wrl, :] #filter daily time series for LOI
            unimp = loidf.loc[(loidf['Sensitivity_Scenario_Code'] == 11) & (loidf['EPP_Scenario_Code'] == 1), :] #filter by no demands, no ift
            scnlist = loidf.groupby(['Sensitivity_Scenario_Code', 'EPP_Scenario_Code']).size().reset_index() #get list of all scenario combinations
            for s in scnlist.index: #loop thru scenarios

                #loitab is table of individual performance metrics for each LOI and scenario combination
                ssc = scnlist.loc[s,'Sensitivity_Scenario_Code'] #human scenario
                esc = scnlist.loc[s, 'EPP_Scenario_Code'] #ecological scenario
                loitab.loc[i, 'LOI'] = l
                loitab.loc[i, 'SSC'] = ssc
                loitab.loc[i, 'ESC'] = esc
                scndf = loidf.loc[(loidf['Sensitivity_Scenario_Code'] == ssc) & (loidf['EPP_Scenario_Code'] == esc), :]
                scnlps = lperr.loc[(lperr['ssc'] == ssc) & (lperr['esc'] == esc),:]

                #calculate performance of meeting 3 types of demands over entire POR
                nday = len(scndf.index)
                loitab.loc[i, 'Entire POR Mean Volumetric for Ecological Demands'] = (scndf['limflow'].sum()) / (scndf['Instream_Flow_Target_CFS'].sum())
                loitab.loc[i, 'Entire POR Frequency of Days for Ecological Demands'] = sum(scndf['Eco Met']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Ecological Demands 90%'] = sum(scndf['Eco Met 90%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Ecological Demands 75%'] = sum(scndf['Eco Met 75%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Ecological Demands 50%'] = sum(scndf['Eco Met 50%']) / nday

                loitab.loc[i, 'Entire POR Mean Volumetric for Subwatershed Human Demands'] = (scndf['limlcdm'].sum()) / (scndf['DT_Demand_e_Local_CFS'].sum())
                loitab.loc[i, 'Entire POR Frequency of Days for Subwatershed Human Demands'] = sum(scndf['Hum Local Met']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Subwatershed Human Demands 90%'] = sum(scndf['Hum Local Met 90%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Subwatershed Human Demands 75%'] = sum(scndf['Hum Local Met 75%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for Subwatershed Human Demands 50%'] = sum(scndf['Hum Local Met 50%']) / nday

                loitab.loc[i, 'Entire POR Mean Volumetric for All Upstream Human Demands'] = (scndf['limaldm'].sum()) / (scndf['DT_Demand_e_CFS'].sum())
                loitab.loc[i, 'Entire POR Frequency of Days for All Upstream Human Demands'] = sum(scndf['Hum All Met']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for All Upstream Human Demands 90%'] = sum(scndf['Hum All Met 90%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for All Upstream Human Demands 75%'] = sum(scndf['Hum All Met 75%']) / nday
                loitab.loc[i, 'Entire POR Frequency of Days for All Upstream Human Demands 50%'] = sum(scndf['Hum All Met 50%']) / nday

                #Performance involving meeting demands from July to September
                sumdf = scndf.loc[scndf['month'].between(7,9),:]
                ndsum = len(sumdf.index)
                loitab.loc[i, 'Dry Season Mean Volumetric for Ecological Demands'] = (sumdf['limflow'].sum()) / (sumdf['Instream_Flow_Target_CFS'].sum())
                loitab.loc[i, 'Dry Season Frequency of Days for Ecological Demands'] = sum(sumdf['Eco Met']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Ecological Demands 90%'] = sum(sumdf['Eco Met 90%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Ecological Demands 75%'] = sum(sumdf['Eco Met 75%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Ecological Demands 50%'] = sum(sumdf['Eco Met 50%']) / ndsum

                loitab.loc[i, 'Dry Season Mean Volumetric for Subwatershed Human Demands'] = (sumdf['limlcdm'].sum()) / (sumdf['DT_Demand_e_Local_CFS'].sum())
                loitab.loc[i, 'Dry Season Frequency of Days for Subwatershed Human Demands'] = sum(sumdf['Hum Local Met']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Subwatershed Human Demands 90%'] = sum(sumdf['Hum Local Met 90%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Subwatershed Human Demands 75%'] = sum(sumdf['Hum Local Met 75%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for Subwatershed Human Demands 50%'] = sum(sumdf['Hum Local Met 50%']) / ndsum

                loitab.loc[i, 'Dry Season Mean Volumetric for All Upstream Human Demands'] = (sumdf['limaldm'].sum()) / (sumdf['DT_Demand_e_CFS'].sum())
                loitab.loc[i, 'Dry Season Frequency of Days for All Upstream Human Demands'] = sum(sumdf['Hum All Met']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for All Upstream Human Demands 90%'] = sum(sumdf['Hum All Met 90%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for All Upstream Human Demands 75%'] = sum(sumdf['Hum All Met 75%']) / ndsum
                loitab.loc[i, 'Dry Season Frequency of Days for All Upstream Human Demands 50%'] = sum(sumdf['Hum All Met 50%']) / ndsum

                # Performance involving meeting demands from October to June
                windf = scndf.loc[~scndf['month'].between(7, 10), :]
                ndwin = len(windf.index)
                loitab.loc[i, 'Not Dry Season Mean Volumetric for Ecological Demands'] = (windf['limflow'].sum()) / (windf['Instream_Flow_Target_CFS'].sum())
                loitab.loc[i, 'Not Dry Season Frequency of Days for Ecological Demands'] = sum(windf['Eco Met']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Ecological Demands 90%'] = sum(windf['Eco Met 90%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Ecological Demands 75%'] = sum(windf['Eco Met 75%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Ecological Demands 50%'] = sum(windf['Eco Met 50%']) / ndwin

                loitab.loc[i, 'Not Dry Season Mean Volumetric for Subwatershed Human Demands'] = (windf['limlcdm'].sum()) / (windf['DT_Demand_e_Local_CFS'].sum())
                loitab.loc[i, 'Not Dry Season Frequency of Days for Subwatershed Human Demands'] = sum(windf['Hum Local Met']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Subwatershed Human Demands 90%'] = sum(windf['Hum Local Met 90%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Subwatershed Human Demands 75%'] = sum(windf['Hum Local Met 75%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for Subwatershed Human Demands 50%'] = sum(windf['Hum Local Met 50%']) / ndwin

                loitab.loc[i, 'Not Dry Season Mean Volumetric for All Upstream Human Demands'] = (windf['limaldm'].sum()) / (windf['DT_Demand_e_CFS'].sum())
                loitab.loc[i, 'Not Dry Season Frequency of Days for All Upstream Human Demands'] = sum(windf['Hum All Met']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for All Upstream Human Demands 90%'] = sum(windf['Hum All Met 90%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for All Upstream Human Demands 75%'] = sum(windf['Hum All Met 75%']) / ndwin
                loitab.loc[i, 'Not Dry Season Frequency of Days for All Upstream Human Demands 50%'] = sum(windf['Hum All Met 50%']) / ndwin

                #Calculate and save off performance of meeting demands in each month
                ecmxmon = scndf.groupby('month').sum()['Eco Met']
                ec90mon = scndf.groupby('month').sum()['Eco Met 90%']
                ec75mon = scndf.groupby('month').sum()['Eco Met 75%']
                ec50mon = scndf.groupby('month').sum()['Eco Met 50%']

                ndmon = scndf.groupby('month').size()

                flwsum = scndf.groupby('month').sum()['limflow']
                iftsum = scndf.groupby('month').sum()['Instream_Flow_Target_CFS']
                # performance of meeting eco demands
                #worst month, whatever month that may be, as well as the month with the worst performance
                loitab.loc[i, 'Worst Month Mean Volumetric for Ecological Demands'] = min(flwsum/iftsum)
                loitab.loc[i, 'Worst Month Mean Volumetric for Ecological Demands month'] = next(iter(flwsum.loc[flwsum / iftsum == min(flwsum / iftsum)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands'] = min(ecmxmon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands month'] = next(iter(ecmxmon.loc[ecmxmon / ndmon == min(ecmxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 90%'] = min(ec90mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 90% month'] = next(iter(ec90mon.loc[ec90mon / ndmon == min(ec90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 75%'] = min(ec75mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 75% month'] = next(iter(ec75mon.loc[ec75mon / ndmon == min(ec75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 50%'] = min(ec50mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Ecological Demands 50% month'] = next(iter(ec50mon.loc[ec50mon / ndmon == min(ec50mon / ndmon)].index.get_values()), None)

                # best month, whatever month that may be plus the month of best performance
                loitab.loc[i, 'Best Month Mean Volumetric for Ecological Demands'] = max(flwsum/iftsum)
                loitab.loc[i, 'Best Month Mean Volumetric for Ecological Demands month'] = next(iter(flwsum.loc[flwsum / iftsum == max(flwsum / iftsum)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands'] = max(ecmxmon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands month'] = next(iter(ecmxmon.loc[ecmxmon / ndmon == max(ecmxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 90%'] = max(ec90mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 90% month'] = next(iter(ec90mon.loc[ec90mon / ndmon == max(ec90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 75%'] = max(ec75mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 75% month'] = next(iter(ec75mon.loc[ec75mon / ndmon == max(ec75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 50%'] = max(ec50mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Ecological Demands 50% month'] = next(iter(ec50mon.loc[ec50mon / ndmon == max(ec50mon / ndmon)].index.get_values()), None)

                #range of best performing month to worst performing month
                loitab.loc[i, 'Monthly Performance Range Mean Volumetric for Ecological Demands'] = max(flwsum / iftsum) - min(flwsum / iftsum)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Ecological Demands'] = max(ecmxmon / ndmon) - min(ecmxmon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Ecological Demands 90%'] = max(ec90mon / ndmon) - min(ec90mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Ecological Demands 75%'] = max(ec75mon / ndmon) - min(ec75mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Ecological Demands 50%'] = max(ec50mon / ndmon) - min(ec50mon / ndmon)

                #standard deviation of monthly performance
                loitab.loc[i, 'Monthly Performance Std Dev Mean Volumetric for Ecological Demands'] = (flwsum/iftsum).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Ecological Demands'] = (ecmxmon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Ecological Demands 90%'] = (ec90mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Ecological Demands 75%'] = (ec75mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Ecological Demands 50%'] = (ec50mon / ndmon).std()

                for m in ndmon.index: #save off each month performance
                    mnam = cal.month_name[m]
                    loitab.loc[i, mnam + ' Mean Volumetric for Ecological Demands'] = flwsum[m] / iftsum[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Ecological Demands'] = ecmxmon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Ecological Demands 90%'] = ec90mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Ecological Demands 75%'] = ec75mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Ecological Demands 50%'] = ec50mon[m] / ndmon[m]


                #do all of the above but for permitted local subwatershed human demands
                hlmxmon = scndf.groupby('month').sum()['Hum Local Met']
                hl90mon = scndf.groupby('month').sum()['Hum Local Met 90%']
                hl75mon = scndf.groupby('month').sum()['Hum Local Met 75%']
                hl50mon = scndf.groupby('month').sum()['Hum Local Met 50%']

                splsum = scndf.groupby('month').sum()['limlcdm']
                dmlsum = scndf.groupby('month').sum()['DT_Demand_e_Local_CFS']


                loitab.loc[i, 'Worst Month Mean Volumetric for Subwatershed Human Demands'] = min(splsum / dmlsum)
                loitab.loc[i, 'Worst Month Mean Volumetric for Subwatershed Human Demands month'] = next(iter(splsum.loc[splsum / dmlsum == min(splsum / dmlsum)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands'] = min(hlmxmon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands month'] = next(iter(hlmxmon.loc[hlmxmon / ndmon == min(hlmxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 90%'] = min(hl90mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 90% month'] = next(iter(hl90mon.loc[hl90mon / ndmon == min(hl90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 75%'] = min(hl75mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 75% month'] = next(iter(hl75mon.loc[hl75mon / ndmon == min(hl75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 50%'] = min(hl50mon/ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for Subwatershed Human Demands 50% month'] = next(iter(hl50mon.loc[hl50mon / ndmon == min(hl50mon / ndmon)].index.get_values()), None)

                loitab.loc[i, 'Best Month Mean Volumetric for Subwatershed Human Demands'] = max(splsum/dmlsum)
                loitab.loc[i, 'Best Month Mean Volumetric for Subwatershed Human Demands month'] = next(iter(splsum.loc[splsum / dmlsum == max(splsum / dmlsum)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands'] = max(hlmxmon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands month'] = next(iter(hlmxmon.loc[hlmxmon / ndmon == max(hlmxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 90%'] = max(hl90mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 90% month'] = next(iter(hl90mon.loc[hl90mon / ndmon == max(hl90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 75%'] = max(hl75mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 75% month'] = next(iter(hl75mon.loc[hl75mon / ndmon == max(hl75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 50%'] = max(hl50mon/ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for Subwatershed Human Demands 50% month'] = next(iter(hl50mon.loc[hl50mon / ndmon == max(hl50mon / ndmon)].index.get_values()), None)

                loitab.loc[i, 'Monthly Performance Range Mean Volumetric for Subwatershed Human Demands'] = max(splsum/dmlsum) - min(splsum/dmlsum)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Subwatershed Human Demands'] = max(hlmxmon / ndmon) - min(hlmxmon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Subwatershed Human Demands 90%'] = max(hl90mon / ndmon) - min(hl90mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Subwatershed Human Demands 75%'] = max(hl75mon / ndmon) - min(hl75mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for Subwatershed Human Demands 50%'] = max(hl50mon / ndmon) - min(hl50mon / ndmon)

                loitab.loc[i, 'Monthly Performance Std Dev Mean Volumetric for Subwatershed Human Demands'] = (splsum / dmlsum).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Subwatershed Human Demands'] = (hlmxmon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Subwatershed Human Demands 90%'] = (hl90mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Subwatershed Human Demands 75%'] = (hl75mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for Subwatershed Human Demands 50%'] = (hl50mon / ndmon).std()

                for m in ndmon.index: #loop through months
                    mnam = cal.month_name[m]
                    loitab.loc[i, mnam + ' Mean Volumetric for Subwatershed Human Demands'] = splsum[m] / dmlsum[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Subwatershed Human Demands'] = hlmxmon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Subwatershed Human Demands 90%'] = hl90mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Subwatershed Human Demands 75%'] = hl75mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for Subwatershed Human Demands 50%'] = hl50mon[m] / ndmon[m]

                # same as above but for all contributing area permitted human demands
                hamxmon = scndf.groupby('month').sum()['Hum All Met']
                ha90mon = scndf.groupby('month').sum()['Hum All Met 90%']
                ha75mon = scndf.groupby('month').sum()['Hum All Met 75%']
                ha50mon = scndf.groupby('month').sum()['Hum All Met 50%']

                spasum = scndf.groupby('month').sum()['limaldm']
                dmasum = scndf.groupby('month').sum()['DT_Demand_e_CFS']

                loitab.loc[i, 'Worst Month Mean Volumetric for All Upstream Human Demands'] = min(spasum / dmasum)
                loitab.loc[i, 'Worst Month Mean Volumetric for All Upstream Human Demands month'] =  next(iter(splsum.loc[splsum / dmlsum == min(splsum / dmlsum)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands'] = min(hamxmon / ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands month'] =  next(iter(hamxmon.loc[hamxmon / ndmon == min(hamxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 90%'] = min(ha90mon / ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 90% month'] = next(iter(ha90mon.loc[ha90mon / ndmon == min(ha90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 75%'] = min(ha75mon / ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 75% month'] = next(iter(ha75mon.loc[ha75mon / ndmon == min(ha75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 50%'] = min(ha50mon / ndmon)
                loitab.loc[i, 'Worst Month Frequency of Days for All Upstream Human Demands 50% month'] = next(iter(ha50mon.loc[ha50mon / ndmon == min(ha50mon / ndmon)].index.get_values()), None)

                loitab.loc[i, 'Best Month Mean Volumetric for All Upstream Human Demands'] = max(spasum / dmasum)
                loitab.loc[i, 'Best Month Mean Volumetric for All Upstream Human Demands month'] =  next(iter(splsum.loc[splsum / dmlsum == max(splsum / dmlsum)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands'] = max(hamxmon / ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands month'] =  next(iter(hamxmon.loc[hamxmon / ndmon == max(hamxmon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 90%'] = max(ha90mon / ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 90% month'] = next(iter(ha90mon.loc[ha90mon / ndmon == max(ha90mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 75%'] = max(ha75mon / ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 75% month'] = next(iter(ha75mon.loc[ha75mon / ndmon == max(ha75mon / ndmon)].index.get_values()), None)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 50%'] = max(ha50mon / ndmon)
                loitab.loc[i, 'Best Month Frequency of Days for All Upstream Human Demands 50% month'] = next(iter(ha50mon.loc[ha50mon / ndmon == max(ha50mon / ndmon)].index.get_values()), None)

                loitab.loc[i, 'Monthly Performance Range Mean Volumetric for All Upstream Human Demands'] = max(spasum / dmasum) - min(spasum / dmasum)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for All Upstream Human Demands'] = max(hamxmon / ndmon) - min(hamxmon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for All Upstream Human Demands 90%'] = max(ha90mon / ndmon) - min(ha90mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for All Upstream Human Demands 75%'] = max(ha75mon / ndmon) - min(ha75mon / ndmon)
                loitab.loc[i, 'Monthly Performance Range Frequency of Days for All Upstream Human Demands 50%'] = max(ha50mon / ndmon) - min(ha50mon / ndmon)

                loitab.loc[i, 'Monthly Performance Std Dev Mean Volumetric for All Upstream Human Demands'] = (spasum / dmasum).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for All Upstream Human Demands'] = (hamxmon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for All Upstream Human Demands 90%'] = (ha90mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for All Upstream Human Demands 75%'] = (ha75mon / ndmon).std()
                loitab.loc[i, 'Monthly Performance Std Dev Frequency of Days for All Upstream Human Demands 50%'] = (ha50mon / ndmon).std()

                for m in ndmon.index:
                    mnam = cal.month_name[m]
                    loitab.loc[i, mnam + ' Mean Volumetric for All Upstream Human Demands'] = spasum[m] / dmasum[m]
                    loitab.loc[i, mnam + ' Frequency of Days for All Upstream Human Demands'] = hamxmon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for All Upstream Human Demands 90%'] = ha90mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for All Upstream Human Demands 75%'] = ha75mon[m] / ndmon[m]
                    loitab.loc[i, mnam + ' Frequency of Days for All Upstream Human Demands 50%'] = ha50mon[m] / ndmon[m]

                #Calculate Impairment by taking the difference in flow between no demands/no IFT scenario and other scenarios
                wrs = (wr['Sensitivity_Scenario_Code'] == ssc) & (wr['EPP_Scenario_Code'] == esc)
                scndf.loc[:, 'Impairment'] = unimp.loc[scndf.index, 'Streamflow_CFS'] - scndf.loc[:, 'Streamflow_CFS']
                scndf.loc[scnlps['newdate'],'Impairment'] = np.nan #take error dates and set to nan
                scndf.loc[:,'Impairment'] = scndf.loc[:,'Impairment'].interpolate() #interpolate impairment between surrounding dates for error dates
                scndf.loc[(scndf.loc[:,'Impairment'] < 0.001) | (unimp.loc[scndf.index, 'Streamflow_CFS'] == 0),'Impairment'] = 0 #rounding error
                #calculate moving average of impairment
                scndf.loc[:,'3 Day Moving Avg Impairment'] = scndf.loc[:, 'Impairment'].rolling( \
                    window=3,center=True,min_periods=1).mean()
                scndf.loc[:,'5 Day Moving Avg Impairment'] = scndf.loc[:, 'Impairment'].rolling( \
                    window=5,center=True,min_periods=1).mean()
                scndf.loc[:,'7 Day Moving Avg Impairment'] = scndf.loc[:, 'Impairment'].rolling( \
                    window=7,center=True,min_periods=1).mean()

                #save impairment back into main daily time series
                wr.loc[wrl & wrs, 'Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index, 'Impairment']
                wr.loc[wrl & wrs, '3 Day Moving Avg Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'3 Day Moving Avg Impairment']
                wr.loc[wrl & wrs, '5 Day Moving Avg Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'5 Day Moving Avg Impairment']
                wr.loc[wrl & wrs, '7 Day Moving Avg Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'7 Day Moving Avg Impairment']
                allmntdef = scndf.groupby('month').mean()['Impairment']
                allmntdef.loc[allmntdef < 0.001] = 0
                sumind = (scndf['month'] >= 7) & (scndf['month'] <= 10)

                #calculate summary values of impairment
                loitab.loc[i, 'Entire POR Mean Impairment'] = scndf.loc[:,'Impairment'].mean() #entire POR
                loitab.loc[i, 'Dry Season Mean Impairment'] = scndf.loc[sumind,'Impairment'].mean() #dry season (July - Sept)
                loitab.loc[i, 'Not Dry Season Mean Impairment'] = scndf.loc[~sumind,'Impairment'].mean() #not dry season
                loitab.loc[i, 'Best Month Mean Impairment'] = allmntdef.max() #best month
                loitab.loc[i, 'Worst Month Mean Impairment'] = allmntdef.min() #worst month
                loitab.loc[i, 'Entire POR Impairment 3 Day Moving Avg Max'] = scndf.loc[:, '3 Day Moving Avg Impairment'].max() #max 3-day MA
                loitab.loc[i, 'Entire POR Impairment 5 Day Moving Avg Max'] = scndf.loc[:, '5 Day Moving Avg Impairment'].max() #max 5-day MA
                loitab.loc[i, 'Entire POR Impairment 7 Day Moving Avg Max'] = scndf.loc[:, '7 Day Moving Avg Impairment'].max() #max 7-day MA
                loitab.loc[i, 'Dry Season Impairment 3 Day Moving Avg Max'] = scndf.loc[sumind, '3 Day Moving Avg Impairment'].max()
                loitab.loc[i, 'Dry Season Impairment 5 Day Moving Avg Max'] = scndf.loc[sumind, '5 Day Moving Avg Impairment'].max()
                loitab.loc[i, 'Dry Season Impairment 7 Day Moving Avg Max'] = scndf.loc[sumind, '7 Day Moving Avg Impairment'].max()
                loitab.loc[i, 'Not Dry Season Impairment 3 Day Moving Avg Max'] = scndf.loc[~sumind, '3 Day Moving Avg Impairment'].max()
                loitab.loc[i, 'Not Dry Season Impairment 5 Day Moving Avg Max'] = scndf.loc[~sumind, '5 Day Moving Avg Impairment'].max()
                loitab.loc[i, 'Not Dry Season Impairment 7 Day Moving Avg Max'] = scndf.loc[~sumind, '7 Day Moving Avg Impairment'].max()

                #highest and lowest mean monthly impairment of moving averages
                allmnt3def = scndf.groupby('month').max()['3 Day Moving Avg Impairment']
                allmnt3def.loc[allmnt3def < 0.001] = 0
                loitab.loc[i, 'Worst Month Impairment 3 Day Moving Avg Max'] = allmnt3def.min()
                loitab.loc[i, 'Best Month Impairment 3 Day Moving Avg Max'] = allmnt3def.max()

                allmnt5def = scndf.groupby('month').max()['5 Day Moving Avg Impairment']
                allmnt5def.loc[allmnt5def < 0.001] = 0
                loitab.loc[i, 'Worst Month Impairment 5 Day Moving Avg Max'] = allmnt5def.min()
                loitab.loc[i, 'Best Month Impairment 5 Day Moving Avg Max'] = allmnt5def.max()

                allmnt7def = scndf.groupby('month').max()['7 Day Moving Avg Impairment']
                allmnt7def.loc[allmnt7def < 0.001] = 0
                loitab.loc[i, 'Worst Month Impairment 7 Day Moving Avg Max'] = allmnt7def.min()
                loitab.loc[i, 'Best Month Impairment 7 Day Moving Avg Max'] = allmnt7def.max()

                for m in allmntdef.index: #save each month's impairment metrics
                    mnam = cal.month_name[m]
                    loitab.loc[i, mnam + ' Mean Impairment'] = allmntdef[m]
                    loitab.loc[i, mnam + ' Impairment 3 Day Moving Avg Max'] = allmnt3def[m]
                    loitab.loc[i, mnam + ' Impairment 5 Day Moving Avg Max'] = allmnt5def[m]
                    loitab.loc[i, mnam + ' Impairment 7 Day Moving Avg Max'] = allmnt7def[m]

                #calculate metrics again for standardized impairment by dividing impairment by no-demand flow
                scndf.loc[:,'Standardized Impairment'] = scndf.loc[:,'Impairment'] / unimp.loc[scndf.index, 'Streamflow_CFS']
                scndf.loc[np.isnan(scndf['Standardized Impairment']), 'Standardized Impairment'] = 0
                scndf.loc[:,'3 Day Moving Avg Standardized Impairment'] = scndf.loc[:, 'Standardized Impairment'].rolling( \
                    window=3,center=True,min_periods=1).mean()
                scndf.loc[:,'5 Day Moving Avg Standardized Impairment'] = scndf.loc[:, 'Standardized Impairment'].rolling( \
                    window=5,center=True,min_periods=1).mean()
                scndf.loc[:,'7 Day Moving Avg Standardized Impairment'] = scndf.loc[:, 'Standardized Impairment'].rolling( \
                    window=7,center=True,min_periods=1).mean()

                #save off to main daily time series
                wr.loc[wrl & wrs, 'Standardized Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index, 'Standardized Impairment']
                wr.loc[wrl & wrs, '3 Day Moving Avg Standardized Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'3 Day Moving Avg Standardized Impairment']
                wr.loc[wrl & wrs, '5 Day Moving Avg Standardized Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'5 Day Moving Avg Standardized Impairment']
                wr.loc[wrl & wrs, '7 Day Moving Avg Standardized Impairment'] = scndf.loc[wr.loc[wrl & wrs,:].index,'7 Day Moving Avg Standardized Impairment']

                #calculate mean monthly standardized impairment
                allmntprp = scndf.groupby('month').mean()['Standardized Impairment']
                allmntprp.loc[(allmntprp < 0)] = 0
                allmntprp.loc[(allmntprp > 1)] = 1

                # calculate summary metrics involving SI
                loitab.loc[i, 'Entire POR Mean Standardized Impairment'] = scndf.loc[:,'Standardized Impairment'].mean()
                loitab.loc[i, 'Dry Season Mean Standardized Impairment'] = scndf.loc[sumind,'Standardized Impairment'].mean()
                loitab.loc[i, 'Not Dry Season Mean Standardized Impairment'] = scndf.loc[~sumind,'Standardized Impairment'].mean()
                loitab.loc[i, 'Best Month Mean Standardized Impairment'] = allmntprp.max()
                loitab.loc[i, 'Worst Month Mean Standardized Impairment'] = allmntprp.min()
                loitab.loc[i, 'Entire POR Standardized Impairment 3 Day Moving Avg Max'] = scndf.loc[:, '3 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Entire POR Standardized Impairment 5 Day Moving Avg Max'] = scndf.loc[:, '5 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Entire POR Standardized Impairment 7 Day Moving Avg Max'] = scndf.loc[:, '7 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Dry Season Standardized Impairment 3 Day Moving Avg Max'] = scndf.loc[sumind, '3 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Dry Season Standardized Impairment 5 Day Moving Avg Max'] = scndf.loc[sumind, '5 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Dry Season Standardized Impairment 7 Day Moving Avg Max'] = scndf.loc[sumind, '7 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Not Dry Season Standardized Impairment 3 Day Moving Avg Max'] = scndf.loc[~sumind, '3 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Not Dry Season Standardized Impairment 5 Day Moving Avg Max'] = scndf.loc[~sumind, '5 Day Moving Avg Standardized Impairment'].max()
                loitab.loc[i, 'Not Dry Season Standardized Impairment 7 Day Moving Avg Max'] = scndf.loc[~sumind, '7 Day Moving Avg Standardized Impairment'].max()

                # calculate monthly SI metrics
                allmnt3prp = scndf.groupby('month').max()['3 Day Moving Avg Standardized Impairment']
                allmnt3prp.loc[(allmnt3prp < 0)] = 0
                allmnt3prp.loc[(allmnt3prp > 1)] = 1
                loitab.loc[i, 'Worst Month Standardized Impairment 3 Day Moving Avg Max'] = allmnt3prp.min()
                loitab.loc[i, 'Best Month Standardized Impairment 3 Day Moving Avg Max'] = allmnt3prp.max()

                allmnt5prp = scndf.groupby('month').max()['5 Day Moving Avg Standardized Impairment']
                allmnt5prp.loc[(allmnt5prp < 0)] = 0
                allmnt5prp.loc[(allmnt5prp > 1)] = 1
                loitab.loc[i, 'Worst Month Standardized Impairment 5 Day Moving Avg Max'] = allmnt5prp.min()
                loitab.loc[i, 'Best Month Standardized Impairment 5 Day Moving Avg Max'] = allmnt5prp.max()

                allmnt7prp = scndf.groupby('month').max()['7 Day Moving Avg Standardized Impairment']
                allmnt7prp.loc[(allmnt7prp < 0)] = 0
                allmnt7prp.loc[(allmnt7prp > 1)] = 1
                loitab.loc[i, 'Worst Month Standardized Impairment 7 Day Moving Avg Max'] = allmnt7prp.min()
                loitab.loc[i, 'Best Month Standardized Impairment 7 Day Moving Avg Max'] = allmnt7prp.max()

                for m in allmntprp.index:
                    mnam = cal.month_name[m]
                    loitab.loc[i, mnam + ' Mean Standardized Impairment'] = allmntprp[m]
                    loitab.loc[i, mnam + ' Standardized Impairment 3 Day Moving Avg Max'] = allmnt3prp[m]
                    loitab.loc[i, mnam + ' Standardized Impairment 5 Day Moving Avg Max'] = allmnt5prp[m]
                    loitab.loc[i, mnam + ' Standardized Impairment 7 Day Moving Avg Max'] = allmnt7prp[m]

                i=i+1
        if (resave == 1): #if data is to be saved again
            print('Saving daily time series to file...')
            wr.to_csv(wrfile)
            print('Done, writing LOI performance table to csv...')
            loitab.to_csv(ltfile)
        else:
            print('Done, not re-saving data...')
        #change columns to be easier to type
        wr = wr.rename(columns={"Sensitivity_Scenario_Code": "SSC", "EPP_Scenario_Code": "ESC",
                                "Date.1": "date", "Water_Month_Type": "WMT", "Streamflow_CFS": "flow"})
    else: #skip calculations, just read from file.
        print('Not performing calculations, just reading from files...')
        if ltonly == 0:
            wr = pd.read_csv(wrfile,index_col=0)
            wr.index = pd.to_datetime(wr.index)
            wr = wr.rename(columns={"Sensitivity_Scenario_Code": "SSC", "EPP_Scenario_Code": "ESC",
                                    "Date.1": "date", "Water_Month_Type": "WMT", "Streamflow_CFS": "flow"})
        else:
            wr = []
        loitab = pd.read_csv(ltfile,index_col=0)

    #give end time to see how long it took
    end = dt.datetime.now()
    print('End: ', end.strftime(format='%I:%M:%S %p'))
    print('Time Elapsed: ',str((end-start).total_seconds() / 60), ' min')
    return wr, loitab



