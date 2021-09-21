#This scenario provides translation between scenario numbers and scenario names.
# Sensitivity Scenario Code = SSC which is human scenario, and
# Ecological Scenario Code = ESC, which is ecological scenario

import pandas as pd
import numpy as np

#this takes a scenario number and returns a name.
def get_scn_name(esc=[0],ssc=[0]):
    #input list of esc or ssc. Example:
    # labels = get_scn_name(esc=code_list) - returns list of ecological scenario names associated with the
    #       list of numbers in code_list. Note: even if code_list is a single value, it must be a list.
    # labels = get_scn_name(ssc=code_list) - returns list of human scenario names associated with the
    #       list of numbers in code_list. Note: even if code_list is a single value, it must be a list.

    out = ''
    if (esc[0] > 0) or (ssc[0] > 0):
        if esc[0] > 0: #provide names as ecological scenario
            esctab = pd.DataFrame(index = np.arange(1,16))
            esctab['name'] = ['No IFT','EPP 10','EPP 25','EPP 50',
            'EPP 75','EPP 90','EPP Max','Tessmann','POF 75%','POF 80%',
            'POF 90%','POF 95%','MPOF','NCIFP','FFM']
            out = esctab.loc[esc,'name'].get_values()
        else: #provide names as human scenario
            ssctab = pd.DataFrame(index = np.arange(1,12))
            ssctab['name'] = ['Baseline','Cnnbs Strg 1 Month',
            'Cnnbs Strg 3 Months','Cnnbs Strg Legal','Cnnbs Dmnd 0x',
            'Cnnbs Dmnd 2x','Cnnbs Dmnd 10x','Cnnbs Junior Priority',
            'eWRIMS Dmnd Rprtd','eWRMS Strg Off','No Demands']
            out = ssctab.loc[ssc,'name'].get_values()
    else:
        print('Must pass inputs')
    return out

#Process text in file with dates of WEAP Errors to get an ecological scenario code and human scenario code
def get_scn_nums(intxt):
    #intxt is a string of the form "[eco scenario name]_SenScn_[human scenario number]"
    ssc = int(intxt[intxt.rfind('_') + 1:len(intxt)])

    esctxt = intxt[0:intxt.find('_')]

    esctab = pd.DataFrame(index=np.arange(1, 16))
    esctab['name'] = ['No IFT', 'EPP 10%', 'EPP 25%', 'EPP 50%',
                      'EPP 75%', 'EPP 90%', 'EPP Max', 'Tessman', 'Perc of Flow: 75', 'Perc of Flow: 80',
                      'Perc of Flow: 90', 'Perc of Flow: 95', 'Modified Percent of Flow',
                      'North Coast IFP', 'Functional Flows']
    esc = esctab.loc[esctab['name'] == esctxt,:].index.get_values()[0]
    return ssc,esc

