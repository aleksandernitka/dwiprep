#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_b0s_topupapplied(sid):

    """
    Extracts all b0s from the topup corrected volume (dwi)
    
    Created on Tue Apr 19 10:27:49 2022

    @author: aleksander nitka
    """

    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    import matplotlib.pyplot as plt
    import os
    from dipy.core.histeq import histeq
    import cmocean
    
    gtab = gradient_table(f'tmp/{sid}_AP.bval', f'tmp/{sid}_AP.bvec')
    
    dwi, affine = load_nifti(os.path.join('tmp', f'{sid}_AP_topup-applied.nii.gz'))
    
    b0s = dwi[:,:,:,gtab.b0s_mask]

    save_nifti(f'tmp/{sid}_AP_b0s_topup-applied.nii.gz', b0s, affine)   
    
    # Control figure PA
    fig1, ax = plt.subplots(2, 5, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.15)
    fig1.suptitle(f'{sid} DWI (post topup) b0s', fontsize = 20)
    
    for i in range(0, b0s.shape[3]):
        
        ax.flat[i].imshow(histeq(b0s[:,:,42,i].T), cmap=cmocean.cm.tarn, interpolation='none',origin='lower')
        ax.flat[i].set_title(f'{i}')
        
    fig1.savefig(os.path.join('tmp', f'{sid}_AP_topup-applied_b0s.png'))
    
mk_b0s_topupapplied(sys.argv[1])
