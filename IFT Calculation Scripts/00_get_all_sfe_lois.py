# Read in SFE LOI characteristics table and calculate bankfull flow using cont. Area relation
import pandas as pd

def get_all_sfe_lois():
    refpth = './Reference Files/'
    sfelois = pd.read_excel(refpth + 'All SFE LOI Characteristics with MAF.xlsx',index_col=0)
    loi = [str(i) for i in sfelois['LOI']]
    sfelois['Outlet LOI'] = sfelois['LOI']
    sfelois['Contributing Area (mi^2)'] = sfelois['Contributing Area']
    sfelois['MAF'] = sfelois['Mean Annual Flow (cfs)']
    sfelois['Qbf'] = 71.5 * sfelois['Contributing Area (mi^2)'] #71.5 cfs/mi^2 according to Darren

    subset = pd.read_excel(refpth + 'Subset SFE LOIs.xlsx')
    sublois = sfelois.loc[subset['SWSID'],:]
    return sublois, loi, sfelois