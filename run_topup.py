#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse

args = argparse.ArgumentParser()
args.add_argument('--slist', help = 'CSV file containing subject ids.', required = True)
args.add_argument('--datain', help = 'Path where the denoised data is stored.', required = True)
args = args.parse_args()

def run_topup(args.slist, args.datain):
    """
    This functions runs all things between denoising and topup with apply topup included

    Parameters
    ----------
    slist : CSV file
        File contianing all subject ids that are to be processed.

    Returns
    -------
    Results of called functions.
    

    Created on Fri Apr 22 23:14:54 2022
    @author: aleksander nitka
    """
    
    from os.path import join, exists
    from os import mkdir
    import numpy as np
    from dwiprep import cp_dwi_files, rm_noise_p2s, mk_gradients
    import subprocess as sb
    from datetime import datetime as dt
    
    if exists('send_telegram.py'):
        from send_telegram import sendtel
        telegram = True
    else:
        telegram = False
      
    subs = np.loadtxt(slist, delimiter = '\n', dtype=str)
    
    RAWDATA = args.datain
    
    if telegram:
        sendtel(f'Denoising started: list {slist}')
    
    for idx, s in enumerate(subs):
        
        print(f'{s} -- {idx} out of {len(subs)}')

        # Perform checks
        if exists(join(RAWDATA, s)) == True:
            
            mkdir(join('tmp', s))
                
        else:
            if telegram:
                sendtel(f'{s} not found in {RAWDATA}')
                
    if telegram:
        sendtel(f'Denoising finished for {args.slist}')


