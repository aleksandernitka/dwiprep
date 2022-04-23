#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def run_denoise(slist):
    """
    Run DWI denoising using DIPY patch2self

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
    
    HMRIDIR = '/mnt/nasips/COST_mri/derivatives/hMRI/'
    RAWDATA = '/mnt/nasips/COST_mri/rawdata/'
    OUTPDIR = '/mnt/nasips/COST_mri/derivatives/dwi/preproc/'
    
    if telegram:
        sendtel('Denoising started')
    
    for idx, s in enumerate(subs):
        
        print(f'{s} -- {idx} out of {len(subs)}')

        # Perform checks
        if exists(join(RAWDATA, s, 'dwi')) == True:
            
            if exists(join(HMRIDIR, s, 'Results', f'{s}_synthetic_T1w.nii')) == True:
                
                mkdir(join('tmp', s))
                
                # conda details
                
                # Copy all required files
                cp_dwi_files(s, HMRIDIR, RAWDATA, f'tmp/{s}')
                
                # Make gradients
                mk_gradients(s)
                
                # Denoise p2s
                rm_noise_p2s(s)
                
                # Sort and move files to derivatives directory
                # move files to derivatives directory
                sb.run(f'cp -r tmp/{s} {OUTPDIR}{s}', shell = True)
                sb.run(f'rm -rf tmp/{s}', shell = True)
                
            else:
                # error no T1s
                with open(f'{s}_error.log', 'a') as e:
                    e.write('error copying T1.')
                    e.close()
            
        else:
            # error no dwi dir in raw
            with open(f'{s}_error.log', 'a') as e:
                e.write('error copying dwi files.')
                e.close()

        with open('denoise_done.log', 'a') as l:
            l.write(f'{dt.now()} {s}\n')
            l.close()
            
                
    if telegram:
        sendtel('Denoising finished')

run_denoise(sys.argv[1])

