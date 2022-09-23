#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join
import matplotlib.pyplot as plt
from dipy.io.image import load_nifti
from dipy.denoise.noise_estimate import estimate_sigma
import numpy as np

args = argparse.ArgumentParser('Compares images from both denoising methods.')
args.add_argument('sub', help='subject ID')
args.add_argument('-i', '--data', help='Data folder', default='data')
args = args.parse_args()

if 'sub-' not in args.sub:
    args.sub = 'sub-' + str(args.sub)

print(f'{args.sub}: plotting and comparing images.')

# Load images
img0, aff0 = load_nifti(join(args.data, args.sub, f'{args.sub}_AP.nii'))
img1, aff1 = load_nifti(join(args.data, args.sub, f'{args.sub}_order-1_gib_p2s.nii'))
img2, aff2 = load_nifti(join(args.data, args.sub, f'{args.sub}_order-2_p2s_gib.nii'))

# Estimate noise for all volumes
sigma0 = [] # RAW image
sigma1 = [] # order 1
sigma2 = [] # order 2
for i in range(img1.shape[-1]):
    sigma0.append(estimate_sigma(img0[:,:,:,i])[0])
    sigma1.append(estimate_sigma(img1[:,:,:,i])[0])
    sigma2.append(estimate_sigma(img2[:,:,:,i])[0])

means = [np.mean(sigma0), np.mean(sigma1), np.mean(sigma2)]
stds = [np.std(sigma0), np.std(sigma1), np.std(sigma2)]

# plotting for the images and residuals
fig1, ax = plt.subplots(1,4,figsize=(16,6), subplot_kw = {'xticks':[], 'yticks':[]})
# Image 0
ax.flat[0].imshow(img0[:,:,50,0].T, cmap='gray', origin='lower')
ax.flat[0].set_title(f'RAW AP\n$\sigma$ = {str(np.round(sigma0[0], 2))}, M = {str(np.round(means[0],2))}, SD = {str(np.round(stds[0],2))}')
# Image 1
ax.flat[1].imshow(img1[:,:,50,0].T, cmap='gray', origin='lower')
ax.flat[1].set_title(f'1. GIBBS then P2S\n$\sigma$ = {str(np.round(sigma1[0], 2))}, M = {str(np.round(means[1],2))}, SD = {str(np.round(stds[1],2))}')
# Image 2
ax.flat[2].imshow(img2[:,:,50,0].T, cmap='gray', origin='lower')
ax.flat[2].set_title(f'2. P2S then GIBBS\n$\sigma$ = {str(np.round(sigma2[0], 2))}, M = {str(np.round(means[1],2))}, SD = {str(np.round(stds[2],2))}')
# Difference np.sqrt((orig - den) ** 2)
ax.flat[3].imshow(np.sqrt(img1[:,:,50,0].T - img2[:,:,50,0].T) ** 2, cmap='gray', origin='lower')
ax.flat[3].set_title('Difference')

fig1.savefig(join(args.data, args.sub, f'{args.sub}_compare.png'))
