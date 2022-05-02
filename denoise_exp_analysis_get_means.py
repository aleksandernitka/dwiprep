from os import listdir as ls
import pandas as pd
from os.path import join
import matplotlib.pyplot as plt

ddir = 'denoising_exp_results'

data_files = [f for f in ls(ddir) if f.startswith('sub-') and f.endswith('.csv')]

for i, f in enumerate(data_files):

    df = pd.read_csv(join(ddir, data_files[i]))

    for b in [0, 700, 1200, 1500, 2500]:
        if b == 0:
            dfm = df[df['bvals_corrected'] == b].agg(['mean'], ignore_index=True)
            dfs = df[df['bvals_corrected'] == b].agg(['std'], ignore_index=True)
        else:
            dfm = dfm.append(df[df['bvals_corrected'] == b].agg(['mean']), ignore_index=True)
            dfs = dfs.append(df[df['bvals_corrected'] == b].agg(['std']), ignore_index=True)

    sid = data_files[i].split('_')[0]

    dfm['subject'] = sid
    dfs['subject'] = sid

    if i == 0:
        dfm_all = dfm
        dfs_all = dfs
    else:
        dfm_all = dfm_all.append(dfm, ignore_index=True)
        dfs_all = dfs_all.append(dfs, ignore_index=True)

dfm_all.to_csv(join(ddir, 'denoising_exp_results_mean.csv'), index=False)
dfs_all.to_csv(join(ddir, 'denoising_exp_results_std.csv'), index=False)

