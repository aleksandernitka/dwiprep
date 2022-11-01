#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join
from dipy.denoise.gibbs import gibbs_removal
from dipy.denoise.patch2self import patch2self
from dipy.io.image import load_nifti, save_nifti
import numpy as np
import matplotlib.pyplot as plt

args = argparse.ArgumentParser('Test: which order of preproc steps is better.')
args.add_argument('sub', help='subject ID')
args.add_argument('order', help='Specify order: 1 - gibbs then patch2self, 2 - patch2self then gibbs')
args.add_argument('-i', '--data', help='Data folder', default='data')
args = args.parse_args()

if 'sub-' not in args.sub:
    args.sub = 'sub-' + str(args.sub)

# Load AP and bvals for AP
dat, aff = load_nifti(join(args.data, args.sub, f'{args.sub}_AP.nii'))
bvals = np.loadtxt(join(args.data, args.sub, f'{args.sub}_AP.bval'))

# plotting function for the images and residuals
def plot_results(s1label, s2label, order, raw, st1, st2, subid=args.sub, datadir=args.data):
    fig1, ax = plt.subplots(2,3,figsize=(12,12), subplot_kw = {'xticks':[], 'yticks':[]})
    # RAW image
    ax.flat[0].imshow(raw[:,:,50,0].T, cmap='gray', origin='lower', vmin=0, vmax=10000)
    ax.flat[0].set_title('Uncorrected b0')
    # Image after Step 1
    ax.flat[1].imshow(st1[:,:,50,0].T, cmap='gray', origin='lower', vmin=0, vmax=10000)
    ax.flat[1].set_title('S1: ' + s1label)
    # Image after Step 2
    ax.flat[2].imshow(st2[:,:,50,0].T, cmap='gray', origin='lower', vmin=-0, vmax=10000)
    ax.flat[2].set_title('S2: ' + s2label)
    # Residuals, Step 1 and RAW
    ax.flat[3].imshow(st1[:,:,50,0].T - raw[:,:,50,0].T, cmap='gray', origin='lower', vmin=-500, vmax=500)
    ax.flat[3].set_title('S1 - RAW Residuals')
    # Residuals Step 2 and Step 1
    ax.flat[4].imshow(st2[:,:,50,0].T - st1[:,:,50,0].T, cmap='gray', origin='lower', vmin=-500, vmax=500)
    ax.flat[4].set_title('S2 - S1 Residuals')
    # Residuals Step 2 and RAW
    ax.flat[5].imshow(st2[:,:,50,0].T - raw[:,:,50,0].T, cmap='gray', origin='lower', vmin=-500, vmax=500)
    ax.flat[5].set_title('S2 - RAW Residuals')
    
    fig1.savefig(join(datadir, subid, f'{subid}_o-{order}_{s1label}-{s2label}_results.png'))



if int(args.order) == 1:
    # run gibbs then p2s
    print('Running gibbs deringing')
    s1 = gibbs_removal(dat, inplace=False, num_processes=-1)
    # save half state:
    save_nifti(join(args.data, args.sub, f'{args.sub}_order-{args.order}_gib.nii'), s1, aff)
    # run patch2self
    print('Running patch2self')
    s2 = patch2self(s1, bvals)
    # save final state
    save_nifti(join(args.data, args.sub, f'{args.sub}_order-{args.order}_gib_p2s.nii'), s2, aff)
    # create plots
    plot_results(s1label = 'GIB', s2label = 'P2S', order = '1', raw = dat, st1 = s1, st2 = s2)

elif int(args.order) == 2:
    # run p2s then gibbs
    print('Running patch2self')
    s1 = patch2self(dat, bvals)
    # save half state
    save_nifti(join(args.data, args.sub, f'{args.sub}_order-{args.order}_p2s.nii'), s1, aff)
    # run gibbs
    print('Running gibbs deringing')
    s2 = gibbs_removal(s1, inplace=False, num_processes=-1)
    # save final data
    save_nifti(join(args.data, args.sub, f'{args.sub}_order-{args.order}_p2s_gib.nii'), s2, aff)
    # create plots
    plot_results(s1label = 'P2S', s2label = 'GIB', order = '2', raw = dat, st1 = s1, st2 = s2)

else:
    print(f'Order: {args.order} -- wrong order.')
    exit()

print(f'{args.sub}: order {args.order} done.')
    
  
    
