#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join
import matplotlib.pyplot as plt
from dipy.io.image import load_nifti
import numpy as np

args = argparse.ArgumentParser('Compares images for visual inspection. Plots three planes from both images and difference between the two.')
args.add_argument('sub', help='subject ID')
args.add_argument('vol1', help='Path to first dwi volume')
args.add_argument('vol2', help='Path to second dwi volume')
args.add_argument('-n1', '--name1', help='What is the 1st volumen name', default='data 1', type=str)
args.add_argument('-n2', '--name2', help='What is the 2nd volumen name', default='data 2', type=str)
args.add_argument('-i', '--data', help='Data folder',default='tmp')
args.add_argument('-t', '--title', help='Title of the plot', default='dwi')
args.add_argument('-f', '--fname', help='Filename: sub-X_FILENAME_vX.png', type=str, default='compare')
args.add_argument('-v', '--vols', help='Volumes to compare', default=[0], nargs='+', type=int)
args.add_argument('-s', '--slice', help='Specify slices to plot', nargs=3, type=int, default=[50, 50, 50])
args.add_argument('-cm', '--cmap', help='Colour map (matplotlib)', default='gray', type=str)
args.add_argument('-c', '--comp', choices=['sub', 'res'], default='sub',\
    help='Comparison Type. What method to use to calculate the difference between images: \
        sub - subtract one from another or res - calulcate squared residuals.')
args = args.parse_args()

if 'sub-' not in args.sub:
    args.sub = 'sub-' + str(args.sub)

print(f'{args.sub}: plotting and comparing images.')
try:
    # Load images
    img0, aff0 = load_nifti(args.vol1)
    img1, aff1 = load_nifti(args.vol2)
except:
    print(f'{args.sub}: Unable to load images for comparison.')
    exit(1)

for v in args.vols:
    # plotting for the images and difference
    fig, ax = plt.subplots(3,3, \
        subplot_kw = {'xticks':[], 'yticks':[]}, \
        sharex=True, sharey=True)
    fig.suptitle(f'{args.sub} {args.title} v {v}', fontsize=16)
    
    # Order of plots goes row by row, plot each plane
    # Image 0
    ax.flat[0].imshow(img0[:,:,args.slice[0],v].T, cmap=args.cmap, origin='lower')
    ax.flat[0].set_title(args.name1)
    ax.flat[3].imshow(img0[:,args.slice[1],:,v].T, cmap=args.cmap, origin='lower')
    ax.flat[6].imshow(img0[args.slice[2],:,:,v].T, cmap=args.cmap, origin='lower')

    # Image 1
    ax.flat[1].imshow(img1[:,:,args.slice[0],v].T, cmap=args.cmap, origin='lower')
    ax.flat[1].set_title(args.name2)
    ax.flat[4].imshow(img1[:,args.slice[1],:,v].T, cmap=args.cmap, origin='lower')
    ax.flat[7].imshow(img1[args.slice[2],:,:,v].T, cmap=args.cmap, origin='lower')

    if args.comp == 'res':
        ax.flat[2].imshow(np.sqrt(img0[:,:,args.slice[0],v].T - img1[:,:,args.slice[0],v].T)**2, cmap=args.cmap, origin='lower')
        ax.flat[2].set_title('Difference')
        ax.flat[5].imshow(np.sqrt(img0[:,args.slice[1],:,v].T - img1[:,args.slice[1],:,v].T)**2, cmap=args.cmap, origin='lower')
        ax.flat[8].imshow(np.sqrt(img0[args.slice[2],:,:,v].T - img1[args.slice[2],:,:,v].T)**2, cmap=args.cmap, origin='lower')
    elif args.comp == 'sub':
        ax.flat[2].imshow(img0[:,:,args.slice[0],v].T - img1[:,:,args.slice[0],v].T, cmap=args.cmap, origin='lower')
        ax.flat[2].set_title('Difference')
        ax.flat[5].imshow(img0[:,args.slice[1],:,v].T - img1[:,args.slice[1],:,v].T, cmap=args.cmap, origin='lower')
        ax.flat[8].imshow(img0[args.slice[2],:,:,v].T - img1[args.slice[2],:,:,v].T, cmap=args.cmap, origin='lower')
    plt.tight_layout()
    fig.savefig(join(args.data, args.sub, f'{args.sub}_{args.fname}_v{v}.png'))
