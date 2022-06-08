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

args = argparse.ArgumentParser(description='Function to run Eddy correction (open mp) and Eddyqc using singularity container with FSL', epilog="by Aleksander Nitka")
args.add_argument('mode', choices=('list', 'subject'), help='Mode of operation.')
args.add_argument('input', help = 'Either a CSV file containing subject ids for list mode or a single subject Id for subject mode')
args.add_argument('datain', help = 'Path where the data is stored.')
args.add_argument('singularity', help = 'Path to singularity container with FSL')
args.add_argument('-w', '--wait', help = 'Number of minutes to wait before the processing of the list starts.', required = False, default = 0, type = int)
args.add_argument('-nt', '--notelegram', help = 'Do not send any telegram messages.', required = False, default = False, action = 'store_true')
args.add_argument('-ev', '--eddyverbose', help = 'Run eddy with verbose flag.', required = False, default = False, action = 'store_true')
args.add_argument('-nclean', '--noclean', help = 'Do not clean up the temporary directory.', required = False, action = 'store_true')
args.add_argument('-ncopy', '--nocopy', help = 'Do not copy the data to the temporary directory.', required = False, action = 'store_true')
args = args.parse_args()

# setting of a delay start, especially useful when running multiple instances of the script
if args.wait > 0:
    print(f'Waiting for {args.wait} minutes. Will start processing at {dt.now() + td(minutes=args.wait)}.')
    sleep(args.wait * 60)

# if telegram notification has been set up, send a message
if args.notelegram:
    print('Telegram messages not required.')
    telegram = False
else:
    if exists('send_telegram.py'):
        from send_telegram import sendtel
        telegram = True
    else:
        print('Could not find telegram script. Will not send any messages.')
        telegram = False

# Check container
if exists(args.singularity):
    # print info about container
    sp.run(f'singularity inspect {args.singularity}', shell=True)    
else:
    print('Container error: singularity container not found.')
    exit(1)

# Check synthstrip wrapper in place:
if exists('synthstrip-singularity'):
    print('Synthstrip wrapper found.')
else:
    print('Synthstrip wrapper not found. Please download from https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/')
    exit(1)

# check if singularity file for synthstrip is in place:
if exists('synthstrip.1.0.sif'):
    print('Singularity file for synthstrip found.')
    sp.run(f'singularity inspect {args.singularity}', shell=True) 
else:
    print('Singularity file for synthstrip not found. Please download from https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/')
    exit(1)

# Determine what to run based on mode
if args.mode == 'list':
    subs = np.loadtxt(args.input, delimiter = '\n', dtype=str)
    # istolate list name
    ln = args.input.split('/')[-1].split('.')[0]
    if telegram:
        sendtel(f'Eddy started: list {ln}')
else:
    if not 'sub-' in args.input:
        args.input = 'sub-' + args.input
    subs = [args.input]
    ln = None
    if telegram:
        sendtel(f'Eddy started: {args.input}')


    
# Add to log - mark list start
with open('eddy_done.log', 'a') as l:
    l.write(f'{dt.now()}\tSTART\t{args.input}\n')    
    l.close()

for idx, s in enumerate(subs):
    
    print(f'{s} -- {idx} out of {len(subs)} from {ln}')
    
    ## -- COPY REQ FILES -- ##
    try:
        mkdir(join('tmp', s))
        
        # Copy all required files:
        fcp = [f'{s}_AP_denoised.nii.gz',\
            f'{s}_PA_denoised.nii.gz',\
            f'{s}_AP.bval',\
            f'{s}_AP.bvec',\
            f'{s}_AP.json',\
            f'{s}_PA.json',\
            f'{s}_AP-PA_topup_fieldcoef.nii.gz'\
            f'{s}_AP-PA_topup_movpar.txt'\
            'acqparams.txt']

        for f in fcp:
            shutil.copy(join(args.datain, s, f'{s}{f}'), join('tmp', s, f'{s}{f}'))

    except:
        
        if telegram:
            sendtel(f'{s}: Unable to copy files for processing.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot copy files\n')    
            l.close()
        break
    
    ## -- MAKE BRAINMASK -- ##
    try:
        sp.run(f'fslroi {s}_AP_b0s.nii.gz {s}_AP_b0s_1.nii.gz 0 1', shell=True)
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
        cmd = f'singularity exec {args.singularity} eddy_openmp \
            --imain=tmp/$1/$1_AP_denoised.nii.gz --mask=tmp/$1/$1_b0_brainmask_syns.nii.gz \
            --acqp=tmp/$1/acqparams.txt --index=tmp/$1/eddyindex.txt --bvecs=tmp/$1/$1_AP.bvec \
            --bvals=tmp/$1/$1_AP.bval --topup=tmp/$1/$1_AP-PA_topup --repol --niter=8 \
            --out=tmp/$1/$1_dwi --json=tmp/$1/$1_AP.json --cnr_maps'

        if args.eddyverbose:
            cmd = cmd + ' --verbose'
        
        sp.run(cmd, shell=True)

    except:
        if telegram:
            sendtel(f'{s}: Eddy process failed.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tEddy failed\n')    
            l.close()
        break

    ## -- RUN EDDYQC -- ##
    try:

        cmd = f'singularity exec {args.singularity} eddy_quad \
            tmp/$1/$1_dwi -idx tmp/$1/eddyindex.txt -par tmp/$1/acqparams.txt \
            -m tmp/$1/$1_brainmask_syns.nii.gz -b tmp/$1/$1_AP.bval \
            -o tmp/$1/eddyqc'
        
        if args.eddyverbose:
            cmd = cmd + ' --verbose'

        sp.run(cmd, shell=True)
    except:
        if telegram:
            sendtel(f'{s}: EddyQC failed.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tEddyQC Failed\n')    
            l.close()
        break
    
    ## -- SAVE TO EXTERNAL -- ##
    if args.nocopy:
        pass
    else:
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

    ## -- REMOVE TMP -- ##
    if args.noclean:
        pass
    else:
        try:
            shutil.rmtree(join('tmp', s))
        except:
            if telegram:
                sendtel(f'{s}: Unable to remove tmp folder.')
            with open('eddy_errors.log', 'a') as l:
                l.write(f'{dt.now()}\t{s}\tCannot remove tmp folder\n')    
                l.close()
            break
