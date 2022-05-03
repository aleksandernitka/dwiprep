#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join, exists
from os import mkdir
import numpy as np
from dwiprep import mk_b0s, mk_acq_params, run_topup, plt_topup, mv_post_topup, \
    run_apply_topup
import subprocess as sb
from datetime import datetime as dt
import shutil

args = argparse.ArgumentParser(description="Function to run steps after denoising up until and including topup adn apply topup.")
args.add_argument('--slist', help = 'CSV file containing subject ids.', required = True)
args.add_argument('--datain', help = 'Path where the denoised data is stored.', required = True)
args = args.parse_args()


"""
This functions runs all things between denoising and topup with apply topup included

Parameters
----------
slist : CSV file
    File contianing all subject ids that are to be processed.
    
datain : Path
    Path to dwi preprocessed data - data will be taken and saved there.

Returns
-------
Results of called functions.


Created on Fri Apr 22 23:14:54 2022
@author: aleksander nitka
"""

if exists('send_telegram.py'):
    from send_telegram import sendtel
    telegram = True
else:
    telegram = False
  
subs = np.loadtxt(args.slist, delimiter = '\n', dtype=str)

print(subs)

RAWDATA = args.datain

if telegram:
    sendtel(f'Denoising started: list {args.slist}')

for idx, s in enumerate(subs):
    
    print(f'{s} -- {idx} out of {len(subs)}')

    # Perform checks
    if exists(join(RAWDATA, s)) == True:
        
        mkdir(join('tmp', s))
        
        # Copy all required files:
        fcp = ['_AP.denoised.nii.gz', '_PA_denoised.nii.gz', '_AP.bval', \
               '_PA.bval', '_AP.bvec', '_AP.json', '_PA.json']
        for f in fcp:
            shutil.copy(join(RAWDATA, s, f'{s}{f}'), join('tmp', s, f'{s}{f}'))
        
        # Extract b0s for topup estimation
        mk_b0s(s)
        
        # Merge b0 volumes to one
        sb.run(f'fslmerge -t tmp/{s}/{s}_AP-PA_b0s tmp/{s}/{s}_AP_b0s tmp/{s}/{s}_PA_b0s', shell = True)
        
        # Create mean b0 images
        sb.run(f'fslmaths tmp/{s}/{s}_AP_b0s -Tmean tmp/{s}/{s}_AP_b0s_mean', shell = True)
        sb.run(f'fslmaths tmp/{s}/{s}_PA_b0s -Tmean tmp/{s}/{s}_PA_b0s_mean', shell = True)
        
        # Make acqparams 
        mk_acq_params(s)
        
        # Run topup
        t = dt.now()
        run_topup(s)
        print(dt.now() - t)
        
        # Cleanup after topup
        mv_post_topup(s)
        
        # Apply topup
        # NB it is NO LONGER SUGGESTED TO  RUN the below, Jesper is not longer recomending this step as the same can be achieved by running eddy with params feed into it https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=FSL;3206abfa.1608
        # However I run this to get an undistorted b0 for brainmask
        run_apply_topup(s)
        
        # Make plots post topup
        plt_topup(s)
        
        # move files to derivatives directory
        # sb.run(f'cp -r tmp/{s} {OUTPDIR}{s}', shell = True)
        # sb.run(f'rm -rf tmp/{s}', shell = True)
        
    else:
        if telegram:
            sendtel(f'{s} not found in {RAWDATA}')
            
if telegram:
    sendtel(f'Denoising finished for {args.slist}')


