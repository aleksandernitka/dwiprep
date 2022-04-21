#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 14:59:53 2022

@author: aleksander
"""


import matplotlib.pyplot as plt
from skimage.feature import canny
from dipy.io.image import load_nifti
import os
from dipy.core.histeq import histeq
import cmocean

i, affine = load_nifti(os.path.join('tmp', f'{sid}_AP_b0s_topup-applied_otsu.nii.gz'))

plt.imshow(histeq(i[:,:,42].T), cmap = cmocean.cm.tarn, interpolation = 'none', origin = 'lower', )

fig1, ax = plt.subplots(2, 3, figsize=(16, 12), subplot_kw={'xticks': [], 'yticks': []})
fig1.subplots_adjust(hspace=0.05, wspace=0.05)

sigmas = [1, 2, 3, 4, 5, 6]

for n, s in enumerate(sigmas):
    
    edg = canny(histeq(i[:,:,42]), sigma = s)
    ax.flat[n].imshow(edg.T, interpolation = 'none', origin = 'lower', cmap='gray')
    
    
