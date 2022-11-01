#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:57:28 2022

@author: aleksander

Plots brainmask (binary) on top of the image used to create it
"""
import argparse
from nilearn import plotting
import matplotlib.pyplot as plt

args = argparse.ArgumentParser(description='Function to plot brain mask for QA', epilog="by Aleksander Nitka")
args.add_argument('mask', help='Path to mask file')
args.add_argument('image', help='Path to image used to create the brainmask')
args.add_argument('out', help='Save output figure as')
args.add_argument('-a', '--alpha', help='Set transparency of a mask overlay as [0-1] (default 0.3)', required=False, default=0.3, type=float)
args.add_argument('-l', '--linewd', help='Set line width of a mask (default 2)', required=False, default=2, type=float)
args.add_argument('-c', '--color', help='Mask color (default yellow)', required=False, default='yellow')
args.add_argument('-f', '--fill', help='Plot mask filled (1) or not (0, default)', required=False, default=0)
args = args.parse_args()

print(args)

sid = args.image.split('/')[-1].split('_')[0]

fig = plt.figure(figsize=(12, 5))
# plot with nilearn
display = plotting.plot_anat(args.image, cut_coords = (0, 0, 50), display_mode='ortho', \
                             cmap='gray', draw_cross = 0, figure = fig, title = f'{sid}')
    
display.add_contours(args.mask, alpha = args.alpha, \
                     antialiased=1, linewidths=args.linewd, \
                    colors=[args.color], filled = args.fill)

display.annotate(scalebar=True)

display.savefig(args.out)
display.close()