#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 14:51:09 2022

@author: admin
"""

from dipy.denoise.gibbs import gibbs_removal
from dipy.io.image import load_nifti
import matplotlib.pyplot as plt
import os

sid='sub-65251'

# Load dwi
dwi, dwi_affine = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))

# degibbs dwi
dwi_dg = gibbs_removal(dwi, inplace=False)

# plot 
fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})

ax.flat[0].imshow(dwi[:, :, 42, 0].T, cmap='gray', origin='lower',vmin=0, vmax=10000)
ax.flat[0].set_title('Uncorrected b0')

ax.flat[1].imshow(dwi_dg[:, :, 42, 0].T, cmap='gray', origin='lower', vmin=0, vmax=10000)
ax.flat[1].set_title('Corrected b0')

ax.flat[2].imshow(dwi_dg[:, :, 42, 0].T - dwi[:, :, 4, 0].T,cmap='gray', origin='lower', vmin=-500, vmax=500)
ax.flat[2].set_title('Gibbs residuals')

plt.show()
fig1.savefig(os.path.join('tmp', f'{sid}_gibbs_supp_b0.png'))


