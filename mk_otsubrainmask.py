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
    from dipy.io.image import load_nifti
    import matplotlib.pyplot as plt
    import nibabel as nib
    import numpy as np
    
    b0, b0_affine = load_nifti(os.path.join('tmp', f'{sid}_dwi_b0_mean.nii.gz'))
    
    # Make mask with median_otsu method, default params
    b0_mask, mask = median_otsu(b0)
    
    # save to nifti
    b0_img = nib.Nifti1Image(b0_mask.astype(np.float32), b0_affine)
    nib.save(b0_img, os.path.join('tmp', f'{sid}_dwi_b0_brain_otsu.nii.gz'))
    mask_img = nib.Nifti1Image(b0_mask.astype(np.float32), b0_affine)
    nib.save(mask_img, os.path.join('tmp', f'{sid}_dwi_b0_brain_mask_otsu.nii.gz'))
    
    # control plot
    fig1, ax = plt.subplots(1, 3, figsize=(16, 6), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(b0[:,:,42].T, interpolation = 'none', origin = 'lower')
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.3, interpolation = 'none', origin = 'lower')
    ax.flat[1].imshow(b0[:,50,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.3, interpolation = 'none', origin = 'lower')
    ax.flat[2].imshow(b0[50,:,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.3, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', f'{sid}_brainmask_otsu_cplot.png'))
    
    
mk_otsubrainmask(sys.argv[1])