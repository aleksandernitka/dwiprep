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
    
    from os.path import join, exists
    from os import mkdir
    import numpy as np
    from dwiprep import cp_dwi_files, rm_noise_p2s, mk_gradients, \
        mk_b0s, mk_acq_params, run_topup, plt_topup, mv_post_topup, \
        run_apply_topup
    import subprocess as sb
    from datetime import datetime as dt  
      
    subs = np.loadtxt(slist, delimiter = '\n', dtype=str)
    
    HMRIDIR = '/mnt/clab/COST_mri/derivatives/hMRI/'
    RAWDATA = '/mnt/clab/COST_mri/rawdata/'
    OUTPDIR = '/mnt/clab/COST_mri/derivatives/dwi/preproc/'
    
    
    for s in subs:
        
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
                
                # Extract b0s
                mk_b0s(s)
                
                # Merge b0 volumes to one
                sb.run(f'fslmerge -t tmp/{s}/{s}_AP-PA_b0s tmp/{s}/{s}_AP_b0s tmp/{s}/{s}_PA_b0s', shell = True)
                
                # Create mean b0 images
                sb.run(f'fslmaths tmp/{s}/{s}_AP_b0s -Tmean tmp/{s}/{s}_AP_b0s_mean', shell = True)
                sb.run(f'fslmaths tmp/{s}/{s}_PA_b0s -Tmean tmp/{s}/{s}_PA_b0s_mean', shell = True)
                
                # Make acq params
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

            
                
        