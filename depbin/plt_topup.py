#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def plt_topup(sid):
    """
    Created on Wed Apr 13 18:22:29 2022

    @author: aleksander
    """
    
    import matplotlib.pyplot as plt
    from dipy.io.image import load_nifti
    import os
    import numpy as np
    from dipy.core.histeq import histeq
    from scipy.ndimage import gaussian_filter as gauss # for blur
    import cmocean

    # load dwi b0s
    dwi_ap, __ = load_nifti(os.path.join('tmp', f'{sid}_AP_b0s_mean.nii.gz'))
    dwi_pa, __ = load_nifti(os.path.join('tmp', f'{sid}_PA_b0s_mean.nii.gz'))
    
    fieldcoef, __ = load_nifti(os.path.join('tmp',f'{sid}_AP-PA_topup_fieldcoef.nii.gz'))
    fout, __ = load_nifti(os.path.join('tmp', f'{sid}_AP-PA_fout.nii.gz'))
    iout,__ = load_nifti(os.path.join('tmp', f'{sid}_AP-PA_iout.nii.gz'))

    sigma = 3  # for smoothing
    cmapx = cmocean.cm.tarn # color map 

    # control plot ap and pa
    fig1, ax = plt.subplots(3, 3, figsize=(8, 6), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)

    
    ax.flat[0].set_title('AP_b0')
    ax.flat[0].imshow(histeq(dwi_ap[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[1].set_title('PA_b0')
    ax.flat[1].imshow(histeq(dwi_pa[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[2].set_title('gauss(rms)')
    rms_diff = np.sqrt((histeq(dwi_ap[:,:,42]) - histeq(dwi_pa[:,:,42])) ** 2)
    ax.flat[2].imshow(gauss(rms_diff.T, sigma), interpolation = 'none', origin = 'lower', cmap = cmapx)
    
    ax.flat[3].imshow(histeq(dwi_ap[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[4].imshow(histeq(dwi_pa[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    rms_diff = np.sqrt((histeq(dwi_ap[:,50,:]) - histeq(dwi_pa[:,50,:])) ** 2)
    ax.flat[5].imshow(gauss(rms_diff.T, sigma), interpolation = 'none', origin = 'lower', cmap = cmapx)
    
    ax.flat[6].imshow(histeq(dwi_ap[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[7].imshow(histeq(dwi_pa[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmapx)
    rms_diff = np.sqrt((histeq(dwi_ap[50,:,:]) - histeq(dwi_pa[50,:,:])) ** 2)
    ax.flat[8].imshow(gauss(rms_diff.T, sigma), interpolation = 'none', origin = 'lower', cmap = cmapx)

    
    fig1.savefig(os.path.join('tmp', f'{sid}_topup_appa_cplot.png'))
    plt.close()
    
    # control plot fieldcoef, fout, iout
    fig2, ax = plt.subplots(1, 3, figsize=(8, 3), subplot_kw={'xticks': [], 'yticks': []})
    fig2.subplots_adjust(hspace=0.01, wspace=0.05)
    ax.flat[0].set_title('fieldcoef')
    ax.flat[0].imshow(fieldcoef[:,:,42].T, interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[1].set_title('fout')
    ax.flat[1].imshow(fout[:,:,42].T, interpolation = 'none', origin = 'lower', cmap = cmapx)
    ax.flat[2].set_title('iout')
    ax.flat[2].imshow(fout[:,:,42].T, interpolation = 'none', origin = 'lower', cmap = cmapx)
    fig2.savefig(os.path.join('tmp', f'{sid}_topup_fico_cplot.png'))
    plt.close()

plt_topup(sys.argv[1])
