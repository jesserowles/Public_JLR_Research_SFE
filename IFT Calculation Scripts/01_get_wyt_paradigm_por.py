#calculate WYTs and plot (if selected)
import datetime as dt
import numpy as np
import pandas as pd
import os
import sys
sys.path.insert(1, './IFT Calculation Scripts')
from read_loi_paradigm_flow_v3 import read_loi_paradigm_flow
from get_all_sfe_lois import get_all_sfe_lois
import matplotlib.pyplot as plt
from matplotlib import cm

make_plot = 1
wytdir = './Unimpaired Flow/Water Year Types/'
sublois, loitab, loi = get_all_sfe_lois()
for l in loitab:
    unimp = read_loi_paradigm_flow(l)
    maflow = unimp.groupby('Water Year').mean()
    maflow['WYT'] = ''
    maflow = maflow[['flow','WYT']]
    dyth = maflow['flow'].quantile(0.33) #dry years are < 33rd percentile
    wtth = maflow['flow'].quantile(0.66) #wet years are > 66th percentile
    maflow.loc[maflow[maflow['flow'] < dyth].index, 'WYT'] = 'Dry'
    maflow.loc[maflow[(maflow['flow'] >= dyth) & (maflow['flow'] < wtth)].index, 'WYT'] = 'Moderate'
    maflow.loc[maflow[maflow['flow'] >= wtth].index, 'WYT'] = 'Wet'
    # maflow.index = maflow.index.strftime('%Y')
    maflow.to_excel(wytdir + 'LOI ' + l + ' WYT.xlsx')

    if make_plot == 1: #makes a bar plot of each Water Year and it's mean annual flow
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        wyts = ['Dry','Moderate','Wet']
        cmap = ['orangered','forestgreen','dodgerblue']
        for w in range(len(wyts)):
            wyt = wyts[w]
            mafwyt = maflow.loc[maflow['WYT'] == wyt,:]
            plt.bar(x=mafwyt.index,height=mafwyt['flow'],color=cmap[w])

        ax.set_xlabel('Water Year')
        ax.set_ylabel('Mean Annual Flow (cfs)')
        ax.set_title('Water Year Type for Each Year in Period of Record\nLOI '+l)
        plt.legend(wyts)
        plt.savefig(wytdir + 'Plots/LOI ' + l + ' WYT.png')
        plt.show()