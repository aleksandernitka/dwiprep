
import argparse

parser = argparse.ArgumentParser(description = 'Given one or two nii or nii.gz images this function will calculate a number of metrics')

parser.add_argument('rawimg', help='Raw, not denoised image')
parser.add_argument('-c', '--compare', help='Run in compare mode. Will calcualte all single image metrics but also those based around image comparison.')

from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.measure import euler_number as euler
from skimage.measure import shannon_entropy as shannon
import numpy as np
from dipy.io.image import load_nifti

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

# load image pair
raw, raff = load_nifti('/mnt/nasips/COST_mri/derivatives/dwi/preproc/sub-16558/sub-16558_AP.nii')
den, daff = load_nifti('/mnt/nasips/COST_mri/derivatives/dwi/preproc/sub-16558/sub-16558_AP_denoised.nii.gz')

# TODO check if images are of the same shape

# meansure snr
img1_snr = []
# measure euler
img1_euler = []
# measure shannon
img1_shannon = []
for i in range(0, raw.shape[3]):
    img1_snr.append(snr(raw[:,:,:,i]))
    img1_euler.append(euler(raw[:,:,:,i]))
    img1_shannon.append(shannon(raw[:,:,:,i]))
    
    
    
    





















