#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def plt_brainmask(sid):
    
    import os
    import matplotlib.pyplot as plt
    from dipy.io.image import load_nifti
    
    mask, __ = load_nifti(os.path.join('tmp', f'{sid}_dwi_b0_brain_mask.nii.gz'))
    dwi, __ = load_nifti(os.path.join('tmp', f'{sid}_dwi_b0.nii.gz'))
    
    
    fig1, ax = plt.subplots(1, 3, figsize=(16, 6), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(dwi[:,:,42].T, interpolation = 'none', origin = 'lower')
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.3, interpolation = 'none', origin = 'lower')
    ax.flat[1].imshow(dwi[:,50,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.3, interpolation = 'none', origin = 'lower')
    ax.flat[2].imshow(dwi[50,:,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.3, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', f'{sid}_brainmask_eddy_cplot.png'))


plt_brainmask(sys.argv[1])