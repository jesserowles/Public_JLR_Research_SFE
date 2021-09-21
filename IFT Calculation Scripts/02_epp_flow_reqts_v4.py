#Calculates EPP IFTs
import sys
sys.path.insert(1, './IFT Calculation Scripts')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os
import datetime as dt
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from dateutil.relativedelta import relativedelta
from add_ts_col import add_ts_col
from get_all_sfe_lois import get_all_sfe_lois

def get_wmt_month_data(wmt,m,timeseries,wmtf, boxd):
    #process and save off values for month/WMT
    aws = wmtf[((wmtf['Month']==m) & (wmtf['WMT']==wmt))] #filter by month & WMT
    aws.index = range(len(aws))
    boxd.append(aws['aws'].values) #save off set of AWS values to plot as boxplot later
    timeseries = pd.concat([timeseries,aws['date'],aws['flow'],aws['aws']],ignore_index=True, axis=1) #save off flow and AWS
    return timeseries, boxd, aws

def get_scen_data(aws, wmtstr, tempdf,ehf_q, ehf_a):
    #This function gets IFTs for each month/WMT combo using EPF
    ehf_a = np.array(ehf_a) #AWS from EPF
    ehf_q = np.array(ehf_q) #Flwo from EPF
    maxloiflow = ehf_q[max(np.where(ehf_a == max(ehf_a))[0])] #find flow where AWS is maximized
    clipa = ehf_a[ehf_q <= maxloiflow] #only look at AWS Values below max AWS flow
    clipq = ehf_q[ehf_q <= maxloiflow] #only look at Flow values below max AWS flow

    awsdfsort = aws.sort_values(by=['aws','flow']) #sort values
    sortflow = awsdfsort['flow'].values
    sortaws = awsdfsort['aws'].values


    quants = np.array([1, 0.9, 0.75, 0.5, 0.25, 0.1]) #list of percentile or quantiles
    scendata = np.array([])
    for i in range(len(quants)):
        flwqnt = aws['flow'].quantile(quants[i]) #get quantile of flow
        if flwqnt >= maxloiflow: #if the quantile flow is greater than the max AWS Flow, set requirement to max AWS flow
            qntflow = maxloiflow
        else: #otherwise, get quantile of AWS, then determine flow that gets this value (below max AWS flow)
            awsqnt = aws['aws'].quantile(quants[i])
            qntflow = np.interp(awsqnt, clipa, clipq)

        scendata = np.append(scendata, qntflow) #add to table

    scendata[scendata > maxloiflow] = maxloiflow #do not set IFT higher than max IFT flow
    tempdf.loc[wmtstr] = np.transpose(scendata)
    return tempdf

startdir = 'IFT Results/' #main location

wmtfile = 'Reference Files/Redwood Creek WMTs WY 1996-2019 v3.xlsx' #file containing WMTs
wmttable = pd.read_excel(wmtfile,index_col=0)
wmttable = wmttable.drop(['flow'],axis=1)

loitab, loi, fultab = get_all_sfe_lois()
wmts = ['Critically Dry','Dry','Below Median','Above Median','Wet','Extremely Wet'] #words to go with WMT numbers
awspct = ['Max','90','75','50','25','10'] #Scenario percentiles for labelling
awslabels = ['AWS_'+x for x in awspct]
month = np.append(np.arange(10, 13), np.arange(1, 10)) #months in order of water year rather than calendar
dates = [(dt.datetime(2020,1,1)+relativedelta(months=+x)).timetuple().tm_yday for x in range(12)] #first of each month day of year
startdate = dt.datetime(1995,10,1) #first day of water year
enddate = dt.datetime(1996,9,30) #last day of water year
dates = pd.date_range(startdate,enddate, freq='MS') #date of first of each month
tupleind = [] #create list of scenario percentile with each month
for i in awslabels:
    for j in dates:
        tupleind.append(tuple((i, j)))
awswmtindex = pd.MultiIndex.from_tuples(tupleind,names=['scenario','TS'])
weaptable = pd.DataFrame(index = awswmtindex)
for p in loi: #loop through LOIs
    filename_ehf = startdir + 'LOI_' + p + '_EHF.xlsx'
    if os.path.isfile(filename_ehf): #if we have an ecological performance function for this location, do calculation
        EHF = pd.read_excel(filename_ehf, index_col=0)
        EHF_a = list(EHF['AWS'])
        EHF_q = list(EHF['Q'])
        scenario_table = pd.DataFrame() #create dataframe for storing IFT for each scenario and month/WMT
        for pct in awspct:
            scenario_table['AWS_' + pct] = []
        loi_results_fold = startdir + 'EPP Results by LOI/LOI ' + p + ' All Results/'
        if not os.path.exists(loi_results_fold):
            os.makedirs(loi_results_fold)

        unimp = read_loi_paradigm_flow(p) #read unimpaired flow
        #add WMT to unimpaired flow table
        wmtflow = unimp.reset_index().merge(wmttable, how="left", on=['Month', 'Year']).set_index(unimp.index)
        wmtflow['monthname'] = wmtflow.index.month_name()
        wmtflow['date'] = wmtflow.index
        wmtflow = wmtflow.dropna() #remove times that don't have WMTs (should be all, but just in case)


        for m in month: # loop through months
            mname = datetime.datetime(2019,m,1).strftime("%B") #get month name
            wmtflow['aws'] = pd.DataFrame(np.interp(wmtflow['flow'], EHF_q, EHF_a),
                 index=wmtflow.index, columns = ['AWS']) #use EPF to turn flow into AWS for each day in month
            monthtimeseries = pd.DataFrame()
            boxdata = []
            for w in range(len(wmts)): #loop through WMTs, see functions above
                wmt = wmts[w]
                monthtimeseries, boxdata, aws_rel = get_wmt_month_data(wmt, m, monthtimeseries, wmtflow,boxdata)
                wmtstr = wmt + ' ' + mname
                scenario_table = get_scen_data(aws_rel,wmtstr,scenario_table, EHF_q, EHF_a)
            #label columns of month time series by WMT for Date, Flow, and AWS
            mtsfinal=monthtimeseries.rename(columns={0:"Extr Dry Date", 1:"Extr Dry Flow", 2:"Extr Dry AWS",
                3:"Dry Date", 4:"Dry Flow", 5:"Dry AWS",
                6:"Below Med Date", 7:"Below Med Flow", 8:"Below Med AWS",
                9:"Above Median Date", 10:"Above Median Flow", 11:"Above Median AWS",
                12:"Wet Date", 13:"Wet Flow", 14:"Wet AWS",
                15:"Extr Wet Date", 16:"Extr Wet Flow", 17:"Extr Wet AWS"})
            wmtlocid = "LOI " + p + ' ' + str(m) + '-' + mname
            mtsfinal.to_excel(loi_results_fold + wmtlocid + '.xlsx')

            #plot boxplots of each WMT AWS
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            ax.boxplot(boxdata)
            ax.set_xlabel("Water Month Type")
            ax.set_ylabel("AWS")
            ax.set_title(wmtlocid)
            plt.xticks(np.arange(6) + 1,labels=wmts, rotation=30)
            fig.tight_layout()
            plt.savefig(loi_results_fold + wmtlocid + ' Box.png')
            plt.close(fig)

        #format for table of IFTs for WEAP
        for i in awslabels:
            for w in range(len(wmts)):
                wmt = wmts[w]
                weaptable.loc[i, p+'_'+str(w+1)] = scenario_table.loc[
                    scenario_table.index.str.find(wmt) == 0, i].get_values()

        scenario_table.to_excel(startdir + 'EPP Results by LOI/LOI ' + p + ' AWS_Scenarios.xlsx')
        print("LOI: " + p + " processed.")
    else: #don't have EPF so fill IFTs with 0
        for i in awslabels:
            for w in range(len(wmts)):
                wmt = wmts[w]
                weaptable.loc[i, p + '_' + str(w + 1)] = np.zeros_like(dates,dtype='int')
        print("LOI: " + p + " not processed. Table populated with 0's.")


for i in awslabels: #finish formatting for WEAP
    weaptablescen = weaptable.loc[i,:]
    weaptablescen = add_ts_col(weaptablescen)
    weaptablescen.to_csv(startdir + 'All LOI EPP ' + i + ' IFTs.csv')

