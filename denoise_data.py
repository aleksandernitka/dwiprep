import pandas as pd
import numpy as np
from os import listdir
from os.path import join, exists

if exists('denoise_test'):
    subs = [f for f in listdir('denoise_test') if f.startswith('sub')]
    print(f'found {len(subs)} subject(s)')

    for i, s in enumerate(subs):
        bvals = np.load(join('denoise_test', s, f'{s}_bvals.npy'))
        s_base = np.load(join('denoise_test', s, f'{s}_sigma_base.npy'))
        s_gauss = np.load(join('denoise_test', s, f'{s}_sigma_ap_gauss.npy'))
        s_lpca = np.load(join('denoise_test', s, f'{s}_sigma_ap_lpca.npy'))
        s_mppca = np.load(join('denoise_test', s, f'{s}_sigma_ap_mppca.npy'))
        s_nlm = np.load(join('denoise_test', s, f'{s}_sigma_ap_nlm.npy'))

        bvals_corrected = []
        for l in bvals:
            if 0 < l < 50:
                bvals_corrected.append(0)
            elif 690 < l < 710:
                bvals_corrected.append(700)
            elif 980 < l < 1015:
                bvals_corrected.append(1000)
            elif 1180 < l < 1215:
                bvals_corrected.append(1200)
            elif 1485 < l < 1515:
                bvals_corrected.append(1500)
            elif 2400 < l < 2515:
                bvals_corrected.append(2500)
            else:
                print(f'{l} not found in sorting')

        df = pd.DataFrame(data={'bvals': bvals,
                                'bvals_corrected': bvals_corrected,
                                's_base': s_base,
                                's_gauss': s_gauss,
                                's_lpca': s_lpca,
                                's_mppca': s_mppca,
                                's_nlm': s_nlm})
        print(df['bvals_corrected'].value_counts())

        for b in [0, 700, 1000, 1200, 1500, 2500]:
            df[df['bvals_corrected'] == b].mean().to_csv(join('denoise_test', s, f'{s}_b{b}_means.csv'))
            df[df['bvals_corrected'] == b].std().to_csv(join('denoise_test', s, f'{s}_b{b}_stdev.csv'))
else:
    print('Unable to find subjects directory')
