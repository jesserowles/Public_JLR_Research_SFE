import pandas as pd
import numpy as np

def get_nearest_loi(i,dlois,masrsp):
    ill = masrsp[masrsp['LOI'] == i][['Lat', 'Lon']]
    lll = masrsp[['Lat', 'Lon']]
    dist2loi = np.sqrt((ill.loc[i, 'Lat'] - lll['Lat']) ** 2 + (ill.loc[i, 'Lon'] - lll['Lon']) ** 2)
    dloisdist = dist2loi[dlois]
    ni = dloisdist.index[dloisdist == min(dloisdist)].values[0]

    return ni
