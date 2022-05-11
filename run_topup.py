#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join, exists
from os import mkdir
import numpy as np
from dwiprep import mk_b0s, mk_acq_params, plt_topup, mk_otsu_brain_mask, mk_bet_brain_mask, comp_masks, mv_post_topup
import subprocess as sb
from datetime import datetime as dt
from datetime import timedelta as td
import shutil
from time import sleep

args = argparse.ArgumentParser(description="Function to run steps after denoising up until and including topup adn apply topup.")
args.add_argument('-l', '--list', help = 'CSV file containing subject ids.', required = True)
args.add_argument('-d', '--datain', help = 'Path where the denoised data is stored.', required = True)
args.add_argument('-w', '--wait', help = 'Number of minutes to wait before the processing of the list starts.', required = False, default = 0, type = int)
args.add_argument('-s', '--singularity', help = '[NOT IMPLEMENTED] Use singularity container.', action = 'store_true', default = False)
args.add_argument('-c', '--container', help = '[NOT IMPLEMENTED] Container path (sif file).', required = False, default = None)
args.add_argument('-i', '--inspect', help = '[NOT IMPLEMENTED] Print and save container inspection outputs (singularity inspect)', required = False, default = False, action = 'store_true')
args = args.parse_args()


"""
TODO
- check copying of files, as sub-15953 has generated errors

Created on Fri Apr 22 23:14:54 2022
@author: aleksander nitka
"""

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
  
subs = np.loadtxt(args.list, delimiter = '\n', dtype=str)

# istolate list name
ln = args.list.split('/')[-1].split('.')[0]

if telegram:
    sendtel(f'Denoising started: list {args.list}')
    
# Add to log - mark list start
with open('topup_done.log', 'a') as l:
    l.write(f'{dt.now()}\tSTART\t{ln}\n')    
    l.close()

for idx, s in enumerate(subs):
    
    print(f'{s} -- {idx} out of {len(subs)} from {ln}')

    try:

        mkdir(join('tmp', s))
        
        # Copy all required files:
        fcp = ['_AP_denoised.nii.gz', '_PA_denoised.nii.gz', '_AP.bval', \
                '_AP.bvec', '_AP.json', '_PA.json']
        for f in fcp:
            shutil.copy(join(args.datain, s, f'{s}{f}'), join('tmp', s, f'{s}{f}'))
        
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
        tp_cmd = f'topup --config=b02b0.cnf --datain=tmp/{s}/acqparams.txt \
        --imain=tmp/{s}/{s}_AP-PA_b0s.nii.gz --out=tmp/{s}/{s}_AP-PA_topup \
        --iout=tmp/{s}/{s}_iout --fout=tmp/{s}/{s}_fout -v \
        --jacout=tmp/{s}/{s}_jac --logout=tmp/{s}/{s}_topup.log \
        --rbmout=tmp/{s}/{s}_xfm --dfout=tmp/{s}/{s}_warpfield'
    
        sb.run(tp_cmd, shell=True)

        dtopup = dt.now() - t
        print(f'Topup duration: {dtopup}')

        with open('topup_times.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\t{ln}\t{dtopup}\n')
            l.close()
        
        # NB it is NO LONGER SUGGESTED TO  RUN APPLY TOPUP, Jesper is not longer recomending this step as the same can be achieved by running eddy with params feed into it https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=FSL;3206abfa.1608
        
        # Make mean b0, this time from the topup corrected data
        sb.run(f'fslmaths tmp/{s}/{s}_iout.nii.gz -Tmean tmp/{s}/{s}_iout_mean.nii.gz', shell = True)
        
        # plot topup correction
        print(f'{dt.now()} {s} from {ln} plotting topup results')
        plt_topup(s)

        # make brainmask bet
        # mk_otsu_brain_mask(s) 
        # make brainmask bet
        # mk_bet_brain_mask(s)
        
        # Compare masks
        # comp_masks(s)

        # Cleanup
        print(f'{dt.now()} {s} from {ln} cleaning up')
        mv_post_topup(s)

        # Move stuff to storage
        print(f'{dt.now()} {s} from {ln} moving to storage')
        sb.run(f'cp -nr tmp/{s}/* /mnt/nasips/COST_mri/derivatives/dwi/preproc/{s}/', shell = True )
        
        # add to log - completed
        with open('topup_done.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\t{ln}\n')
            l.close()
        
        # Clean tmp dir
        print(f'{dt.now()} {s} from {ln} cleaning tmp dir')
        sb.run(f'rm -rf tmp/{s}', shell = True)
        
        
    except:
        if telegram:
            sendtel(f'{s} from {ln} cannot be processed {ln}')
        with open('topup_errors.log', 'a') as e:
            e.write(f'{dt.now()}\t{s}\t{ln}\n')
            e.close()
            
if telegram:
    sendtel(f'Denoising finished for {ln}')
    with open('topup_done.log', 'a') as l:
        l.write(f'{dt.now()}\tEND\t{ln}\n')
        l.close()
