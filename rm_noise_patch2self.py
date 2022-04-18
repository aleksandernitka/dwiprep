#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uses dipy's patch2self to denoise the dwi image, relies on scikit-klearn so install that first.
After processing the AP volume (around 3h on Macbook Pro 2017) it will process PA 
with bvals set as [5,5,5,5,5]. 

Then it procuces a control plots for all volumes in both sets.

Saves both as sub-xxxx_AP_denoised in tmp


Created on Fri Apr 15 15:20:23 2022

@author: admin
"""
from dipy.io.image import load_nifti, save_nifti
import matplotlib.pyplot as plt
import numpy as np
import os
from shutil import rmtree as rmt
from dipy.denoise.patch2self import patch2self

sid='sub-65251'

# Load dwi
dwi_ap, dwi_ap_affine = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))
dwi_pa, dwi_pa_affine = load_nifti(os.path.join('tmp', f'{sid}_PA.nii'))

# load bval
bvals_ap = np.loadtxt(os.path.join('tmp', f'{sid}_AP.bval'))
bvals_pa = np.array([5,5,5,5,5])

dwi_ap_den = patch2self(dwi_ap, bvals_ap, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)
dwi_pa_den = patch2self(dwi_pa, bvals=bvals_pa, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)

# Plot all volumes
s = 42 # slice
png_dir = os.path.join('tmp', f'{sid}_p2s_pngs')

if os.path.exists(png_dir):
    rmt(png_dir)
    os.mkdir(png_dir)
else:
    os.mkdir(png_dir)


# plots for AP
for i, vs in enumerate(range(0, dwi_ap_den.shape[3])):


    # computes the residuals
    rms_diff = np.sqrt((dwi_ap[:,:,s,vs] - dwi_ap_den[:,:,s,vs]) ** 2)

    fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})

    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    fig1.title(f'{sid} AP vol={vs} bval={int(bvals_ap[i])}', fontsize =20)

    ax.flat[0].imshow(dwi_ap[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[0].set_title(f'Original, vol {vs}')
    ax.flat[1].imshow(dwi_ap_den[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[1].set_title('Denoised Output')
    ax.flat[2].imshow(rms_diff.T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[2].set_title('Residuals')
    
    fig1.savefig(os.path.join(png_dir, f'{sid}_ap_bv-{int(bvals_pa[i])}_v-{vs}.png'))
   
# Plots for PA
for i, vs in enumerate(range(0, dwi_pa_den.shape[3])):


    # computes the residuals
    rms_diff = np.sqrt((dwi_pa[:,:,s,vs] - dwi_pa_den[:,:,s,vs]) ** 2)

    fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})

    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    fig1.suptitle(f'{sid} PA vol={vs} bval={int(bvals_pa[i])}', fontsize=20)

    ax.flat[0].imshow(dwi_pa[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[0].set_title(f'Original, vol {vs}')
    ax.flat[1].imshow(dwi_pa_den[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[1].set_title('Denoised Output')
    ax.flat[2].imshow(rms_diff.T, cmap='gray', interpolation='none',origin='lower')
    ax.flat[2].set_title('Residuals')
    
    fig1.tight_layout()
    fig1.savefig(os.path.join(png_dir, f'{sid}_pa_bv-{int(bvals_pa[i])}_v-{vs}.png'))

# Save NII
save_nifti(os.path.join('tmp', f'{sid}_AP_denoised.nii.gz'), dwi_ap_den, dwi_ap_affine)
save_nifti(os.path.join('tmp', f'{sid}_PA_denoised.nii.gz'), dwi_pa_den, dwi_pa_affine)

           