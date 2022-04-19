#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_b0s(sid):
    """
    Extracts all b0s from the AP.nii and saves it as AP_b0s.nii.gz
    Control plot with all b0s is saved as AP_b0s.png
    
    Created on Tue Apr 19 10:27:49 2022

    @author: aleksander nitka
    """
    
    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    import matplotlib.pyplot as plt
    import os
    
    gtab = gradient_table(f'tmp/{sid}_AP.bval', f'tmp/{sid}_AP.bvec')
    
    dwi_ap, affine_ap = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))
    
    b0s_ap = dwi_ap[:,:,:,gtab.b0s_mask]
    
    
    # Control figure
    fig1, ax = plt.subplots(2, 5, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    fig1.suptitle(f'{sid} AP b0s', fontsize = 20)
    
    for i in range(0, b0s_ap.shape[3]):
        
        ax.flat[i].imshow(b0s_ap[:,:,42,i].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[i].set_title(f'{i}')
        
    fig1.savefig(os.path.join('tmp', f'{sid}_b0s_pa.png'))
    
    # Save AP b0s
    save_nifti(f'tmp/{sid}_AP_b0s.nii.gz', b0s_ap, affine_ap)   
    
    
mk_b0s(sys.argv[1])