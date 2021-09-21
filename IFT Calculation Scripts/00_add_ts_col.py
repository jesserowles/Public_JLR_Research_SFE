

def add_ts_col(tab):
#adds column for TS as first column of DataFrame as formatted date
    tab['TS'] = tab.index.strftime('%m/%d/%Y')
    cols = tab.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    tab = tab[cols]
    return tab