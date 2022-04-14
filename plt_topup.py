#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def plt_topup(sid):
    """
    Created on Wed Apr 13 18:22:29 2022

    @author: aleksander
    """
    
    import matplotlib.pyplot as plt
    from dipy.io.image import load_nifti
    import os

    # load dwi b0s
    dwi_ap_b0, affine_ap = load_nifti(os.path.join('tmp', f'{sid}_AP_b0.nii.gz'))
    dwi_pa_b0, affine_pa = load_nifti(os.path.join('tmp', f'{sid}_PA_b0.nii.gz'))
    dwi_co_b0, affine_co = load_nifti(os.path.join('tmp', f'{sid}_dwi.nii.gz'))
    
    # control plot ap and pa
    fig1, ax = plt.subplots(3, 3, figsize=(8, 6), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].set_title('AP_b0')
    ax.flat[0].imshow(dwi_ap_b0[:,:,42].T, interpolation = 'none', origin = 'lower')
    ax.flat[1].set_title('PA_b0')
    ax.flat[1].imshow(dwi_pa_b0[:,:,42].T, interpolation = 'none', origin = 'lower')
    ax.flat[2].set_title('Topup')
    ax.flat[2].imshow(dwi_co_b0[:,:,42, 0].T, interpolation = 'none', origin = 'lower')
    
    ax.flat[3].imshow(dwi_ap_b0[:,50,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[4].imshow(dwi_pa_b0[:,50,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[5].imshow(dwi_co_b0[:,50,:, 0].T, interpolation = 'none', origin = 'lower')
    
    ax.flat[6].imshow(dwi_ap_b0[50,:,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[7].imshow(dwi_pa_b0[50,:,:].T, interpolation = 'none', origin = 'lower')
    ax.flat[8].imshow(dwi_co_b0[50,:,:, 0].T, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', f'{sid}_topup_cplot.png'))

