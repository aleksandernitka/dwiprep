#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Created on Tue May 31 13:00:38 2022
@author: aleksander nitka
"""

import argparse
from os.path import join, exists
from time import sleep
from datetime import datetime as dt
from datetime import timedelta as td
import numpy as np
import subprocess as sp
import shutil

# TODO add mutually exclusive (?) to run a single subject rather than a list

args = argparse.ArgumentParser(description="Function to run eddy correction and eddyqc using singularity container with FSL and DIPY 1.5.0.")
args.add_argument('-l', '--list', help = 'CSV file containing subject ids.', required = True)
args.add_argument('-d', '--datain', help = 'Path where the data is stored.', required = True)
args.add_argument('-s', '--singularity', help = 'Path to singularity container with FSL and DIPY.', required = True)
args.add_argument('-w', '--wait', help = 'Number of minutes to wait before the processing of the list starts.', required = False, default = 0, type = int)
args = args.parse_args()

# setting of a delay start, especially useful when running multiple instances of the script
if args.wait > 0:
    print(f'Waiting for {args.wait} minutes. Will start processing at {dt.now() + td(minutes=args.wait)}.')
    sleep(args.wait * 60)
# if telegram notification has been set up, send a message
if exists('send_telegram.py'):
    from send_telegram import sendtel
    telegram = True
else:
    telegram = False

# Check container
if exists(args.singularity):
    # print info about container
    # TODO if the below breaks, stop function as singularity cannot be located in the system
    sp.run(f'singularity inspect {args.singularity}')
else:
    # TODO not sure if this is the right way to exit if fails
    exit()

subs = np.loadtxt(args.list, delimiter = '\n', dtype=str)

# istolate list name
ln = args.list.split('/')[-1].split('.')[0]

if telegram:
    sendtel(f'Eddy started: list {args.list}')
    
# Add to log - mark list start
with open('eddy_done.log', 'a') as l:
    l.write(f'{dt.now()}\tSTART\t{ln}\n')    
    l.close()

for idx, s in enumerate(subs):
    
    print(f'{s} -- {idx} out of {len(subs)} from {ln}')
    
    ## -- COPY REQ FILES -- ##
    try:
        mkdir(join('tmp', s))
        
        # Copy all required files:
        # TODO Topup files
        fcp = ['_AP_denoised.nii.gz', '_PA_denoised.nii.gz', '_AP.bval', \
                '_AP.bvec', '_AP.json', '_PA.json', '_AP_b0s.nii.gz', 'acqparams.txt', \
                ]
        for f in fcp:
            shutil.copy(join(args.datain, s, f'{s}{f}'), join('tmp', s, f'{s}{f}'))
        
        # copy all required files
        # cp the following: 
        # TODO
        files = ['acqparams.txt', 'AP_denoised.nii', 'AP_denoised.json', 'AP.bvals', 'AP.bvec', 'topup generated files', 'AP_b0s']
    except:
        
        if telegram:
            sendtel(f'{s}: Unable to copy files for processing.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot copy files\n')    
            l.close()
        break
    
    ## -- MAKE BRAINMASK -- ##
    try:
        sp.run(f'fslroi {s}_AP_b0s.nii.gz {s}_AP_b0s_1.nii.gz 0 1')
        # make brain mask with SynthStrip container
        sp.run(f'python mri_synthstrip -i tmp/{s}/{s}_AP_b0s_1.nii.gz -o tmp/{s}/{s}_AP_b0s_1_brain_syns.nii.gz -m tmp/{s}/{s}_brainmask_syns.nii.gz ', shell=True)

        # TODO plot mask for control
        
    except:
        if telegram:
            sendtel(f'{s}: Unable to create at least one of the masks.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot make masks\n')    
            l.close()
        break
    
    ## -- RUN EDDY -- ##    
    try:
        # run eddy with outlier replacement --repol, slice to volume correction
        sp.run(f'singularity exec {args.singularity} eddy_openmp \
            --imain=tmp/$1_AP.nii.gz --mask=tmp/$1_dwi_b0_brain_mask_otsu.nii.gz \
            --acqp=tmp/acqparams.txt --index=tmp/eddyindex.txt --bvecs=tmp/$1_AP.bvec \
            --bvals=tmp/$1_AP.bval --topup=tmp/res_topup --repol --niter=8 \
            --out=tmp/$1_dwi_cor --verbose --json=tmp/$1_AP.json --cnr_maps', shell=True)

    except:
        if telegram:
            sendtel(f'{s}: Eddy process failed.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tEddy failed\n')    
            l.close()
        break

    ## -- RUN EDDYQC -- ##
    try:
        sp.run(f'singularity exec {args.singularity} eddy_quad \
            tmp/$1_dwi_cor -idx tmp/eddyindex.txt -par tmp/acqparams.txt \
            -m tmp/$1_dwi_b0_brain_mask_otsu.nii.gz -b tmp/$1_AP.bval \
            -v -o tmp/eddyqc', shell=True)
    except:
        if telegram:
            sendtel(f'{s}: EddyQC failed.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tEddyQC Failed\n')    
            l.close()
        break
    
    ## -- SAVE TO EXTERNAL -- ##
    try:
        # TODO
        pass
    except:
        if telegram:
            sendtel(f'{s}: Unable to copy files back to storage.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot copy files back\n')    
            l.close()
        break