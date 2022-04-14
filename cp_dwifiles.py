#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


def cp_dwifiles(sid, hmri, rawdata, where):
    
    """
    Created on Wed Apr 13 17:46:00 2022
    
    Copy all files needed for preprocessing in dwi, make sure all dirs exist


    @author: aleksander
    """
    
    import os
    import shutil
    
    if 'sub' not in sid:
        sid = 'sub-' + str(sid)
       
    # get all dwi files for pp
    bfs = [f for f in os.listdir(os.path.join(rawdata, sid, 'dwi')) if '.DS_' not in f]

    # get all _AP_ files
    fsdwi = [f for f in bfs if '_SBRef_' not in f and '_ADC_' not in f and '_TRACEW_' not in f and '_ColFA_' not in f and '_FA_' not in f]
    if len(fsdwi) != 6:
        print(f'{sid} has {len} dwi files')
        return None

    # cp dwi to tmp
    for f in fsdwi:
        if '_AP_' in f:
            fn = f'{sid}_AP.{f.split(".")[-1]}'
        elif '_PA_' in f:
            fn = f'{sid}_PA.{f.split(".")[-1]}'
        
        shutil.copy(os.path.join(rawdata, sid, 'dwi', f), os.path.join(where, fn))

    # cp t1 to tmp
    try:
        shutil.copy(os.path.join(hmri, sid, 'Results', f'{sid}_synthetic_T1w.nii'), os.path.join(where, f'{sid}_T1w.nii'))
    except:
        print(f'{sid} error copying t1w')
        return None
    
cp_dwifiles(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])