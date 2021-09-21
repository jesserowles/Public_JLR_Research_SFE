#For some reason, the April 2021 SEWAM results have the eco and human scenario codes set to 1 for all scenarios
# this script fixes them, assuming they are in the same order using the results broken into individual
# scenarios
import numpy as np
import os
import pandas as pd

os.chdir('../Redwood Creek Results 2021.04.06')
escs = np.arange(1,15)
sscs = np.arange(1,12)
cols = pd.read_csv('SFER_Instance_Results_Template.csv').columns
scnum = 5
compres = pd.DataFrame(columns=cols)
for e in escs:
    for s in sscs:
        if (s < 11) or ((s == 11) and (e==1)):
            scnstr = 'Scenario'+"{0:03}".format(scnum)+'.csv'
            print('Processing ' +scnstr + ' with ESC = ' + str(e) + ' and SSC = ' + str(s))
            scn = pd.read_csv(scnstr,names=cols)
            scn.columns = cols
            scn.index = pd.to_datetime(scn['Date'])
            scn['Sensitivity_Scenario_Code'] = s
            scn['EPP_Scenario_Code'] = e
            compres = compres.append(scn)
            scnum = scnum + 1
compres.to_csv('SFER_Complete_Results_File.csv')
os.chdir('process_rsps') #reset directory to location where