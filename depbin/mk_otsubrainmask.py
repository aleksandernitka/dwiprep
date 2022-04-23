#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 11:43:15 2022

@author: aleksander
"""

import sys

def mk_otsubrainmask(sid):
    
    import os
    from dipy.segment.mask import median_otsu
    from dipy.io.image import load_nifti, save_nifti
    import matplotlib.pyplot as plt
    from dipy.core.histeq import histeq
    import cmocean
    import numpy as np
    
    b0, b0_affine = load_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_mean.nii.gz'))
    
    # Make mask with median_otsu method, default params
    b0_mask, mask = median_otsu(b0)
    
    # save to nifti
    save_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_otsu.nii.gz'), b0_mask, b0_affine)
    save_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_otsu_mask.nii.gz'), mask.astype(np.float32), b0_affine)
    
    # control plot
    fig1, ax = plt.subplots(1, 3, figsize=(8, 3), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(histeq(b0[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[1].imshow(histeq(b0[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[2].imshow(histeq(b0[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', f'{sid}_brainmask_otsu.png'))

    
mk_otsubrainmask(sys.argv[1])