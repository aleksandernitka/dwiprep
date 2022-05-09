#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os.path import join, exists
from os import mkdir
import numpy as np
from dwiprep import mk_b0s, mk_acq_params, plt_topup, mk_otsu_brain_mask, mk_bet_brain_mask, comp_masks, mv_post_topup
import subprocess as sb
from datetime import datetime as dt
import shutil

args = argparse.ArgumentParser(description="Function to run steps after denoising up until and including topup adn apply topup.")
args.add_argument('-l', '--list', help = 'CSV file containing subject ids.', required = True)
args.add_argument('-d', '--datain', help = 'Path where the denoised data is stored.', required = True)
args.add_argument('-s', '--singularity', help = '[NOT IMPLEMENTED] Use singularity container.', action = 'store_true', default = False)
args.add_argument('-c', '--container', help = '[NOT IMPLEMENTED] Container path (sif file).', required = False, default = None)
args.add_argument('-i', '--inspect', help = '[NOT IMPLEMENTED] Print and save container inspection outputs (singularity inspect)', required = False, default = False, action = 'store_true')
args = args.parse_args()


"""
Created on Fri Apr 22 23:14:54 2022
@author: aleksander nitka
"""

if exists('send_telegram.py'):
    from send_telegram import sendtel
    telegram = True
else:
    telegram = False
  
subs = np.loadtxt(args.list, delimiter = '\n', dtype=str)

datain = args.datain

if telegram:
    sendtel(f'Denoising started: list {args.list}')
    
# Add to log - mark list start
with open('topup_done.log', 'a') as l:
    l.write(f'{dt.now()}\tSTART\t{datain}\n')    
    l.close()

for idx, s in enumerate(subs):
    
    print(f'{s} -- {idx} out of {len(subs)}')

    # Perform checks
    if exists(join(datain, s)) == True:
        
        mkdir(join('tmp', s))
        
        # Copy all required files:
        fcp = ['_AP_denoised.nii.gz', '_PA_denoised.nii.gz', '_AP.bval', \
               '_AP.bvec', '_AP.json', '_PA.json']
        for f in fcp:
            shutil.copy(join(datain, s, f'{s}{f}'), join('tmp', s, f'{s}{f}'))
        
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
            l.write(f'{dt.now()}\t{s}\t{datain}\t{dtopup}\n')
            l.close()
        
        # NB it is NO LONGER SUGGESTED TO  RUN APPLY TOPUP, Jesper is not longer recomending this step as the same can be achieved by running eddy with params feed into it https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=FSL;3206abfa.1608
        
        # Make mean b0, this time from the topup corrected data
        sb.run(f'fslmaths tmp/{s}/{s}_iout.nii.gz -Tmean tmp/{s}/{s}_iout_mean.nii.gz', shell = True)
        
        # plot topup correction
        print(f'{dt.now()} {s} plotting topup results')
        plt_topup(s)

        # make brainmask bet
        # mk_otsu_brain_mask(s) 
        # make brainmask bet
        # mk_bet_brain_mask(s)
        
        # Compare masks
        # comp_masks(s)

        # Cleanup
        print(f'{dt.now()} {s} cleaning up')
        mv_post_topup(s)

        # Move stuff to storage
        print(f'{dt.now()} {s} moving to storage')
        sb.run(f'cp -nr tmp/{s}/* {s}', shell = True )
        
        # add to log - completed
        with open('topup_done.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\t{datain}\n')
            l.close()
        
        # Clean tmp dir
        print(f'{dt.now()} {s} cleaning tmp dir')
        sb.run(f'rm -rf tmp/{s}', shell = True)
        
        
    else:
        if telegram:
            sendtel(f'{s} not found in {datain}')
            with open('topup_errors.log', 'a') as e:
                e.write(f'{dt.now()}\t{s}\t{datain}\n')
                e.close()
            
if telegram:
    sendtel(f'Denoising finished for {args.list}')
    with open('topup_done.log', 'a') as l:
        l.write(f'{dt.now()}\tEND\t{datain}\n')
        l.close()
