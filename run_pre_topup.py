#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def run_list_pre_topup(slist):
    """
    Run DWI preprocessing up to topup

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
    
    from os.path import join, exists, makedir
    import numpy as np
    from dwiprep import cp_dwi_files, rm_noise_p2s, mk_gradients, mk_b0s, mk_acq_params
    import subprocess as sb
        
    subs = np.loadtxt(slist, delimiter = '\n', dtype=str)
    
    HMRIDIR = ''
    RAWDATA = ''
    QUALDIR = ''
    
    for s in subs:
        
        # Perform checks
        if exists(join(RAWDATA, s, 'dwi')) == True:
            
            if exists(join(HMRIDIR, s, 'Results', f'{s}_synthetic_T1w.nii')) == True:
                
                makedir(join('tmp', s))
                
                # Copy all required files
                cp_dwi_files(s, HMRIDIR, RAWDATA, f'tmp/{s}')
                
                # Make gradients
                
                # Denoise p2s
                
                # Extract b0s
                
                # Merge b0 volumes to one
                
                # Create mean b0 images
                
                # Make acq params
                
                # Run topup
                
                # Apply topup
                
                # Make plots post topup
                
                # Sort and move files to derivatives directory
                
            else:
                # TODO error no T1s
                with open(f'{s}_error.log', 'a') as e:
                    e.write('error copying T1.')
                    e.close()
            
        else:
            # TODO error no dwi dir in raw
            with open(f'{s}_error.log', 'a') as e:
                e.write('error copying dwi files.')
                e.close()

            
                
        