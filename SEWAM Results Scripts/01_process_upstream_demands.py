#This function takes WEAP results and obtains the reach setting parameters associated with demands
#including UDV, UDD, UDP, UDA, UDM, UDL, UDUA, UDUM, UDUL, and UDPS
import numpy as np
import pandas as pd
from simpledbf import Dbf5
import os
import sys
sys.path.insert(1,'./SEWAM Results Scripts')
from get_nearest_loi import get_nearest_loi
sys.path.insert(1,'./IFT Calculation Scripts')
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow

#This is the demands calculated at each location that is input to WEAP for permitted demands
rawdem = pd.read_excel('./Reference Files/RC and SFER Human Demands.xlsx',sheet_name="Raw Data- SFER")
dlois = np.unique(rawdem['Subwatershed ID'])

#This document stores a table of results in the Baseline/No IFT scenario for each location. It
# must be baseline to get the proper amount of permitted and unpermitted demands under normal
# conditions.
timedem = pd.read_csv('./Reference Files/SFER_Results_BaselineMGMT_NoIFT_Criteria.csv')

#Current RSP list without Demand-based RSPs by LOI with downstream LOI and contributing area
masrsppath = './Reference Files/Master RSP List No Demands.xlsx'
masrsp = pd.read_excel(masrsppath) #assumed to have CA already
masrsp.index = masrsp['LOI']
masrsp = masrsp.drop('LOI check', axis =1)

#Add demand calculated variables with no data values
demrsps = ['UDV','UDD','UDP','UDA','UDM','UDL','UDUA','UDUM','UDUL','UDPS']
masdem = pd.concat([masrsp,pd.DataFrame(columns=demrsps)],sort=False)
masdem[demrsps]=-1 #initialize all to -1 so we have a no data value

#Convert date to date datatype
timedem['Date'] = pd.to_datetime(timedem['Date'])
# Loop through all LOIs we have time series of demands for
alltimelois = np.unique(timedem['LOI'])
for i in alltimelois:
    print(i)
    #Get unimpaired flow for LOI
    unimp = read_loi_paradigm_flow(str(i))
    loitdem = timedem.loc[timedem['LOI']==i,:] #filter demand table by LOI

    #Get mean monthly flow by taking average of every day in each month in POR
    sumyrdem = loitdem.groupby([pd.DatetimeIndex(loitdem['Date']).month,
                     pd.DatetimeIndex(loitdem['Date']).year]).mean()
    #Take max of calendar month over POR (weird in February) for permitted and unpermitted (should be the same in every month)
    pmon = sumyrdem.unstack()['DT_Demand_e_CFS'].max(axis=1) #permitted
    umon = sumyrdem.unstack()['DT_Demand_C_CFS'].max(axis=1) #unpermitted

    #all demands = permitted + unpermitted
    amon = pmon + umon

    #mean annual demands
    aan = amon.mean() #all
    uan = umon.mean() #unpermitted
    pan = pmon.mean() #permitted

    # Now calculate each demand-related RSP
    #UDV - Total Value - Mean of Mean Monthly to get mean annual demand
    masdem.loc[i,'UDV'] = aan

    #UDD - Unpermitted or Permitted dominant
    if (pmon.sum() > umon.sum()):
        masdem.loc[i,'UDD'] = 'P'
    else:
        masdem.loc[i,'UDD'] = 'U'

    #UDP - Permitted Type dominant (e.g., irrigation, municipal, etc.)
    ploidem = rawdem[rawdem['Subwatershed ID'] == i]
    ni = -1

    # have to do some checking since not all LOIs have eWRIMS demands.
    if (len(ploidem.index)==0): # LOI isn't in eWRIMS table
        uiv = masrsp[masrsp['dnLOI']==i]['LOI'].values # get upstream LOI
        div = masrsp[masrsp['LOI']==i]['dnLOI'].values # get downstream LOI
        if not (len(uiv) == 0) and not (len(div) == 0): #If both up and downstream are listed in master RSP list
            ui = uiv[0]
            di = div[0]

            if (ui in dlois) and (di in dlois): #if both are in eWRIMS table
                #use the one that is closer using Lat/Lon
                ill = masrsp[masrsp['LOI'] == i][['Lat','Lon']]
                dll = masrsp[masrsp['LOI'] == di][['Lat', 'Lon']]
                ull = masrsp[masrsp['LOI'] == ui][['Lat', 'Lon']]
                dd = np.sqrt((ill.loc[i,'Lat']-dll.loc[di,'Lat'])**2 + (ill.loc[i,'Lon']-dll.loc[di,'Lon'])**2)
                ud = np.sqrt((ill.loc[i,'Lat']-ull.loc[ui,'Lat'])**2 + (ill.loc[i,'Lon']-ull.loc[ui,'Lon'])**2)
                if (ud > dd):
                    ni = di
                else:
                    ni = ui

            elif ui in dlois: #if only upstream LOI is in eWRIMS sheet, use it
                ni = ui
            elif di in dlois: #if only downstream LOI is in eWRIMS sheet, use it
                ni = di
            else: #if neither are in eWRIMS sheet, find the closest to Lat/Lon
                ni = get_nearest_loi(i,dlois,masrsp)

        elif not (len(uiv) == 0): #only upstream LOI is in master RSP list
            ui = uiv[0]
            if ui in dlois: #also in eWRIMS sheet, so use it
                ni = ui
            else: #if it's not in eWRIMS sheet, find closest via Lat/Lon
                ni = get_nearest_loi(i, dlois, masrsp)
        elif not (len(div) == 0): #only upstream LOI is in master RSP list
            di = div[0]
            if di in dlois: #also in eWRIMS sheet, so use it
                ni = di
            else: #if it's not in eWRIMS sheet, find closest via Lat/Lon
                ni = get_nearest_loi(i, dlois, masrsp)
        else: #neither are in master RSP list, find closest via Lat/Lon
            ni = get_nearest_loi(i, dlois, masrsp)
        print("Using new location ",ni," for dominant permitted type")
        ploidem = rawdem[rawdem['Subwatershed ID'] == ni]

    # add up for each permitted use, set max as UDP value
    ploiuse = ploidem.groupby('BU Group').sum()['Per_Scn_Annual_DT']
    masdem.loc[i,'UDP'] = ploiuse.index[ploiuse == ploiuse.max()][0]

    #UDA - Total Demand per Unit Area
    loica = masrsp.loc[masrsp['LOI'] == i,'Contributing Area'].values[0]
    masdem.loc[i,'UDA'] = aan/loica

    #UDUA - Proportion Unpermitted to area
    masdem.loc[i, 'UDUA'] = uan / loica

    #UDM - Proportion of Mean Annual Flow
    loimaf = unimp.groupby('Water Year').mean()['flow'].mean()
    masdem.loc[i,'UDM'] = aan/loimaf

    #UDUM - Proportion of Mean Annual Flow
    masdem.loc[i,'UDUM'] = uan/loimaf

    #UDL - Proportion of Lowest Monthly Flow
    loilmf = unimp.groupby('Month').mean()['flow'].min()
    masdem.loc[i, 'UDL'] = aan/loilmf

    #UDUL - Proportion Unpermitted to Lowest Monthly Flow
    masdem.loc[i,'UDUL'] = uan/loilmf

    #UDPS - Proportion Unpermitted to Permitted in Summer (July to September)
    strmon = 7
    endmon = 9
    usum = umon[(umon.index <= endmon) & (umon.index >= strmon)].mean()
    psum = pmon[(pmon.index <= endmon) & (pmon.index >= strmon)].mean()
    if psum == 0:
        udps = -1
    else:
        udps = usum / psum
    masdem.loc[i,'UDPS'] = udps
masdem.to_csv('./Reference Files/Master RSP List.csv')
