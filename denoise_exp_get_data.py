import pandas as pd
import numpy as np
from os import listdir
from os.path import join, exists
from dipy.io.image import load_nifti as load

from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.measure import euler_number as euler
from skimage.measure import shannon_entropy as shannon
from dipy.denoise.noise_estimate import estimate_sigma

"""from matplotlib import pyplot as plt
from dipy.core.histeq import histeq
import cmocean"""

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

def calc_metrics(img):
    
    # Calculate single img metrics
    m_sig = []
    m_snr = []
    m_eul = []
    m_sha = []
    # Calcualte comparison metrics
    m_psnr = []
    m_ssim = []
    m_mser = []
    
    for v in range(0, img.shape[3]):
        m_sig.append(estimate_sigma(img[:,:,:,v], N = 32)[0])
        m_snr.append(snr(img[:,:,:,v]))
        m_eul.append(euler(img[:,:,:,v]))
        m_sha.append(shannon(img[:,:,:,v]))
        
        m_psnr.append(psnr(ibase[:,:,:,v], img[:,:,:,v]))
        m_ssim.append(ssim(ibase[:,:,:,v], img[:,:,:,v]))
        m_mser.append(mse(ibase[:,:,:,v], img[:,:,:,v]))
        
    return m_sig, m_snr, m_eul, m_sha, m_psnr, m_ssim, m_mser

edir ='/mnt/nasips/aleksander/experiments/data/denoise_compare/'
edir = '/Users/admin/x2goSwap/'

if exists(edir):
    subs = [f for f in listdir(edir) if f.startswith('sub')]
    subs = ['sub-17188']
    print(f'found {len(subs)} subject(s)')

    # for each subject
    for i, s in enumerate(subs):
        print(f'Processing {s}: {i} out of {len(subs)}')
        
        # Load base image and calculate 
        ibase, __ = load(join(edir, s, f'{s}_AP.nii'))
        
        # calculate image metrics for base image
        base_sig = []
        base_snr = []
        base_eul = []
        base_sha = []
        
        for v in range(0, ibase.shape[3]):
            base_sig.append(estimate_sigma(ibase[:,:,:,v], N=32)[0])
            base_snr.append(snr(ibase[:,:,:,v]))
            base_eul.append(euler(ibase[:,:,:,v]))
            base_sha.append(shannon(ibase[:,:,:,v]))
            
        np.save(join(edir, s, f'{s}_base_sigma.npy'), base_sig)
        np.save(join(edir, s, f'{s}_base_snr.npy'), base_snr)
        np.save(join(edir, s, f'{s}_base_euler.npy'), base_eul)
        np.save(join(edir, s, f'{s}_base_shannon.npy'), base_sha)
            
        # for the rest of images
        # set filename suffixes and data name prefixes
        fnames = ['_ap_gauss.nii.gz', '_ap_lpca.nii.gz', '_ap_mppca.nii.gz', \
                  '_ap_nlm.nii.gz', '_ap_mrtrix.nii.gz', '_AP_denoised.nii.gz']
        dnames = ['gauss', 'lpca', 'mppca', 'nlm', 'mrtrix', 'p2s']
        
        for j, f in enumerate(fnames):
            
            print(f'Processing file: {s}{f}')
            
            # Load image
            img, __ = load(join(edir, s, f'{s}{f}'))
            
            # Calculate metrics
            xsig, xsnr, xeuler, xshan, xpsnr, xssim, xmse = calc_metrics(img)
            
            # Save metrics to file
            np.save(join(edir, s ,f'{s}_{dnames[j]}_sigma.npy'), xsig)
            np.save(join(edir, s, f'{s}_{dnames[j]}_snr.npy'), xsnr)
            np.save(join(edir, s, f'{s}_{dnames[j]}_euler.npy'), xeuler)
            np.save(join(edir, s, f'{s}_{dnames[j]}_shannon.npy'), xshan)
            np.save(join(edir, s, f'{s}_{dnames[j]}_psnr.npy'), xpsnr)
            np.save(join(edir, s, f'{s}_{dnames[j]}_ssim.npy'), xssim)
            np.save(join(edir, s, f'{s}_{dnames[j]}_mse.npy'), xmse)
                        
            # Save as local variables
            globals()[f'{dnames[j]}_sigma'] = xsig
            globals()[f'{dnames[j]}_snr'] = xsnr
            globals()[f'{dnames[j]}_euler'] = xeuler
            globals()[f'{dnames[j]}_shannon'] = xshan
            globals()[f'{dnames[j]}_psnr'] = xpsnr
            globals()[f'{dnames[j]}_ssim'] = xssim
            globals()[f'{dnames[j]}_mse'] = xmse
            
            # Save image - so we can plot the comparisons
            # TODO plot comparisons btw the images
            # globals()[f'{dnames[j]}_nii'] = img
            
            del xsig, xsnr, xeuler, xshan, xpsnr, xssim, xmse, img

        # load nosie sigma vals calcucalated during preprocessing.
        bvals = np.load(join(edir, s, f'{s}_bvals.npy'))
        

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
                                'base_sigma': base_sig,
                                'base_snr': base_snr,
                                'base_shannon': base_sha,
                                'base_euler': base_sha,
                                'gauss_sigma': gauss_sigma,
                                'gauss_snr': gauss_snr,
                                'gauss_shannon': gauss_shannon,
                                'gauss_euler': gauss_euler,
                                'gauss_psnr': gauss_psnr,
                                'gauss_ssim': gauss_ssim,
                                'gauss_mse': gauss_mse,
                                'lpca_sigma': lpca_sigma,
                                'lpca_snr': lpca_snr,
                                'lpca_shannon': lpca_shannon,
                                'lpca_euler': lpca_euler,
                                'lpca_psnr': lpca_psnr,
                                'lpca_ssim': lpca_ssim,
                                'lpca_mse': lpca_mse,
                                'mppca_sigma': mppca_sigma,
                                'mppca_snr': mppca_snr,
                                'mppca_shannon': mppca_shannon,
                                'mppca_euler': mppca_euler,
                                'mppca_psnr': mppca_psnr,
                                'mppca_ssim': mppca_ssim,
                                'mppca_mse': mppca_mse,
                                'nlm_sigma': nlm_sigma,
                                'nlm_snr': nlm_snr,
                                'nlm_shannon': nlm_shannon,
                                'nlm_euler': nlm_euler,
                                'nlm_psnr': nlm_psnr,
                                'nlm_ssim': nlm_ssim,
                                'nlm_mse': nlm_mse,
                                'mrtrix_sigma': mrtrix_sigma,
                                'mrtrix_snr': mrtrix_snr,
                                'mrtrix_shannon': mrtrix_shannon,
                                'mrtrix_euler': mrtrix_euler,
                                'mrtrix_psnr': mrtrix_psnr,
                                'mrtrix_ssim': mrtrix_ssim,
                                'mrtrix_mse': mrtrix_mse,
                                'p2s_sigma': p2s_sigma,
                                'p2s_snr': p2s_snr,
                                'p2s_shannon': p2s_shannon,
                                'p2s_euler': p2s_euler,
                                'p2s_psnr': p2s_psnr,
                                'p2s_ssim': p2s_ssim,
                                'p2s_mse': p2s_mse})
        
        df.to_csv(join(edir, s, f'{s}_metrics.csv'), index=False)

else:
    print('Unable to find subjects directory')
