#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_indexeddy(sid):
    
    """
    Eddy requires index file with has the same amount of rows as the dwi has volumes
    """
    
    import os
    from dipy.io.image import load_nifti
    
    dwi, __ = load_nifti(os.path.join('tmp', f'{sid}_AP_denoised.nii.gz'))
    vols = dwi.shape[3]
    
    #print(f'{sid} {vols} detected')
    
    with open(os.path.join('tmp', 'eddyindex.txt'), 'w') as i:
        for l in range(1, vols+1):
            i.write('1 ')
    i.close()
    
mk_indexeddy(sys.argv[1])