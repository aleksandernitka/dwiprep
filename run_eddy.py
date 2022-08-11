#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO:
+ Add degibbs 
+ add another run_ for qc websites

Requires:
+ dipy 1.5
+ fsl
+ nibabel
+ synthstrip container
+ singularity

Created on Tue May 31 13:00:38 2022
@author: aleksander nitka
"""

import argparse
from os.path import join, exists
from os import mkdir
from datetime import datetime as dt
import numpy as np
import subprocess as sp
import shutil

args = argparse.ArgumentParser(description='Function to run Eddy correction (open mp) and Eddyqc using singularity container with FSL', epilog="by Aleksander Nitka")
args.add_argument('mode', choices=('list', 'subject', 'l', 's'), help='Mode of operation.')
args.add_argument('input', help = 'Either a CSV file containing subject ids for list mode or a single subject Id for subject mode')
args.add_argument('datain', help = 'Path where the data is stored.')
args.add_argument('-fsl', '--fsl', help = 'Path to FSL container.', default = 'fsl.sif')
args.add_argument('-dipy', '--dipy', help = 'Path to DIPY container.', default = 'dipy.sif')
args.add_argument('-nil', '--nilearn', help = 'Path to NILENEAR container.', default = 'nilearn.sif')
args.add_argument('-upd', '--updateme', help="Send telegram updates every X subjects", type=int, default=0)
args.add_argument('-nt', '--notelegram', help = 'Do not send any telegram messages.', required = False, default = False, action = 'store_true')
args.add_argument('-ev', '--eddyverbose', help = 'Run eddy with verbose flag.', required = False, default = False, action = 'store_true')
args.add_argument('-nclean', '--noclean', help = 'Do not clean up the temporary directory.', required = False, action = 'store_true')
args.add_argument('-ncopy', '--nocopy', help = 'Do not copy the data to the temporary directory.', required = False, action = 'store_true')
args = args.parse_args()

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

# Check if all conrainers are in place:
conts = [args.fsl, args.dipy, args.nilearn]
for c in conts:
    if not exists(c):
        print('Could not find container: ' + c)
        exit(1)

# Check synthstrip wrapper in place:
if exists('synthstrip-singularity'):
    print('Synthstrip wrapper found.')
else:
    print('Synthstrip wrapper not found. Please download from https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/')
    exit(1)

# Determine what to run based on mode
if args.mode in ['l','list']:
    subs = np.loadtxt(args.input, delimiter = '\n', dtype=str)
    # istolate list name
    ln = args.input.split('/')[-1].split('.')[0]
    if telegram:
        sendtel(f'Eddy started: list {ln}')
elif args.mode in ['s', 'subject']:
    if not 'sub-' in args.input:
        args.input = 'sub-' + args.input
    subs = [args.input]
    ln = None
    if telegram:
        sendtel(f'Eddy started subject: {args.input}')
else:
    print(f'Mode of operation {args.mode} not recognised, choose a correct mode.')
    exit()

# Add to log - mark list start
with open('eddy_done.log', 'a') as l:
    l.write(f'{dt.now()}\tSTART\t{args.input}\n')    
    l.close()

for idx, s in enumerate(subs):
    
    if args.updateme != 0:
        if telegram:
            if idx % args.updateme == 0:
                sendtel(f'Eddy update: started subject {s}; {idx}/{len(subs)}')

    print(f'{s} -- {idx+1} out of {len(subs)}')
    
    ## -- COPY REQ FILES -- ##
    try:
        mkdir(join('tmp', s))
        # Copy all data to in folder, as this is not overwritten it will be removed
        # and only new files not in 'in' will be kept and moved to archive
        mkdir(join('tmp', s, 'in'))
        
        # Copy all required files:
        fcp = [f'{s}_AP_denoised.nii.gz',\
            f'{s}_PA_denoised.nii.gz',\
            f'{s}_AP.bval',\
            f'{s}_AP.bvec',\
            f'{s}_AP.json',\
            f'{s}_PA.json',\
            f'{s}_AP-PA_topup_fieldcoef.nii.gz',\
            f'{s}_AP-PA_topup_movpar.txt',\
            'acqparams.txt']

        for i in fcp:
            shutil.copy(join(args.datain, s, i), join('tmp', s, 'in', i))

    except:
        
        if telegram:
            sendtel(f'{s}: Unable to copy files for processing.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot copy files\n')    
            l.close()
        #break
    
    ## -- MAKE BRAINMASK -- ##
    try:
        sp.run(f'singularity exec {args.fsl} fslroi \
               tmp/{s}/in/{s}_AP_denoised.nii.gz tmp/{s}/{s}_AP_b0s_1.nii.gz 0 1', \
               shell=True)
            
        # make brain mask with SynthStrip container
        sp.run(f'python synthstrip-singularity \
            -i tmp/{s}/{s}_AP_b0s_1.nii.gz \
            -o tmp/{s}/{s}_AP_b0s_1_brain_syns.nii.gz \
            -m tmp/{s}/{s}_brainmask_syns.nii.gz ', shell=True)

        sp.run(f'singularity run {args.nilearn} python plt_mask.py tmp/{s}/{s}_brainmask_syns.nii.gz \
               tmp/{s}/{s}_AP_b0s_1.nii.gz tmp/{s}/{s}_MASKPLT.png', shell=True)
        
    except:
        if telegram:
            sendtel(f'{s}: Unable to create brainmasks.')
        with open('eddy_errors.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tCannot make mask\n')    
            l.close()
        break
    
    ## -- MAKE INDEX -- ##
    try:
        sp.run(f'singularity run {args.dipy} python mk_eddyi.py \
               tmp/{s}/in/{s}_AP_denoised.nii.gz', shell=True)
    except:
        pass
    
    
    ## -- RUN EDDY -- ##    
    try:
        # run eddy with outlier replacement --repol, slice to volume correction
        cmd = f'singularity exec {args.fsl} eddy_openmp \
            --imain=tmp/{s}/in/{s}_AP_denoised.nii.gz --mask=tmp/{s}/{s}_brainmask_syns.nii.gz \
            --acqp=tmp/{s}/in/acqparams.txt --index=tmp/{s}/eddyindex.txt --bvecs=tmp/{s}/in/{s}_AP.bvec \
            --bvals=tmp/{s}/in/{s}_AP.bval --topup=tmp/{s}/in/{s}_AP-PA_topup --repol --niter=8 \
            --out=tmp/{s}/{s}_dwi --json=tmp/{s}/in/{s}_AP.json --cnr_maps'

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

        cmd = f'singularity exec {args.fsl} eddy_quad \
            tmp/{s}/{s}_dwi -idx tmp/{s}/eddyindex.txt -par tmp/{s}/in/acqparams.txt \
            -m tmp/{s}/{s}_brainmask_syns.nii.gz -b tmp/{s}/in/{s}_AP.bval \
            -o tmp/{s}/eddyqc'
        
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
            # remove the files that are already in the archive
            sp.run(f'rm -rf tmp/{s}/in', shell=True)
            # copy files to external drive
            sp.run(f'cp -r tmp/{s}/* {join(args.datain, s)}', shell=True)
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
