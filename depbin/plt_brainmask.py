#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def plt_brainmask(sid):
    
    import os
    import matplotlib.pyplot as plt
    from dipy.io.image import load_nifti
    from dipy.core.histeq import histeq
    import cmocean
    
    mask, __ = load_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_bet_mask.nii.gz'))
    dwi, __ = load_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_mean.nii.gz'))
    
    
    fig1, ax = plt.subplots(1, 3, figsize=(8, 3), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(histeq(dwi[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[1].imshow(histeq(dwi[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[2].imshow(histeq(dwi[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', f'{sid}_brainmask_bet.png'))


plt_brainmask(sys.argv[1])