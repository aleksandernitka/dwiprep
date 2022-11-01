#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 14:47:38 2022

@author: aleksander

Creates index for Eddy.

"""
import argparse
from os.path import join
from dipy.io.image import load_nifti

args = argparse.ArgumentParser(description='Function to create index for Eddy, relies on DIPY 1.5.0', epilog="by Aleksander Nitka")
args.add_argument('ap', help='Path to AP volume to create index from')
args = args.parse_args()

dwi, __ = load_nifti(args.ap)
vols = dwi.shape[3]

sid = args.ap.split('/')[-1].split('_')[0]

with open(join('tmp', sid, 'eddyindex.txt'), 'w') as i:
    for l in range(1, vols+1):
        i.write('1 ')
i.close()