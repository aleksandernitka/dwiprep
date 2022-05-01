import pandas as pd
import numpy as np
from os import listdir
from os.path import join, exists
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.measure import euler_number as euler
from skimage.measure import shannon_entropy as shannon
import numpy as np
from dipy.io.image import load_nifti as load

def snr(a, axis=None, ddof=0):
    """
    The signal-to-noise ratio of the input data.
    Returns the signal-to-noise ratio of `a`, here defined as the mean
    divided by the standard deviation.
    source: https://github.com/scipy/scipy/blob/v0.16.0/scipy/stats/stats.py#L1963
    Parameters
    ----------
    a : array_like
        An array_like object containing the sample data.
    axis : int or None, optional
        Axis along which to operate. Default is 0. If None, compute over
        the whole array `a`.
    ddof : int, optional
        Degrees of freedom correction for standard deviation. Default is 0.
    Returns
    -------
    s2n : ndarray
        The mean to standard deviation ratio(s) along `axis`, or 0 where the
        standard deviation is 0.
    """
    a = np.asanyarray(a)
    m = a.mean(axis)
    sd = a.std(axis=axis, ddof=ddof)
    return np.where(sd == 0, 0, m/sd)

edir ='/mnt/nasips/aleksander/experiments/data/denoise_compare/'

if exists(edir):
    subs = [f for f in listdir(edir) if f.startswith('sub')]
    print(f'found {len(subs)} subject(s)')

    # for each subject
    for i, s in enumerate(subs):
        print(f'Processing {s}: {i} out of {len(subs)}')

        # load nosie sigma vals calcucalated during preprocessing.
        bvals = np.load(join(edir, s, f'{s}_bvals.npy'))
        s_base = np.load(join(edir, s, f'{s}_sigma_base.npy'))
        s_gauss = np.load(join(edir, s, f'{s}_sigma_ap_gauss.npy'))
        s_lpca = np.load(join(edir, s, f'{s}_sigma_ap_lpca.npy'))
        s_mppca = np.load(join(edir, s, f'{s}_sigma_ap_mppca.npy'))
        s_nlm = np.load(join(edir, s, f'{s}_sigma_ap_nlm.npy'))

        # Load images and perform further calculations
        ibase, abase = load(join(edir, s, f'{s}_AP.nii'))
        igauss, agauss = load(join(edir, s, f'{s}_ap_gauss.nii'))
        ilpca, alpca = load(join(edir, s, f'{s}_ap_lpca.nii'))
        imppca, amppca = load(join(edir, s, f'{s}_ap_mppca.nii'))
        inlm, anlm = load(join(edir, s, f'{s}_ap_nlm.nii'))
        ip2s, ap2s = load(join(edir, s ,f'{s}_AP_denoised.nii'))

        # Calculate all single image metrics
        def single_i_metrics(img):
            # Calculate metrics
            psnr_img = psnr(img, img, data_range=img.max() - img.min())
            ssim_img = ssim(img, img, data_range=img.max() - img.min())
            mse_img = mse(img, img)
            euler_img = euler(img)
            shannon_img = shannon(img)
            snr_img = snr(img)

            # Return metrics
            return psnr_img, ssim_img, mse_img, euler_img, shannon_img, snr_img



        # bvals are not precisely reported, so we need to interpolate them.
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
