#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_affinetable(sid):
    
    """
    Takes affine matrix from AP dwi raw file and makes a html table
    so it can be put into a QA report 
    
    Created on Fri Apr 15 09:58:08 2022

    @author: aleksander
    """
    
    import os
    from dipy.io.image import load_nifti
    import pandas as pd
    
    __, aff = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))
    # Save affine tx matrix as html
    pd_aff = pd.DataFrame(aff)
    pd_aff.to_html(os.path.join('tmp', 'dwi_affine.html'), index=False, header=False)
    
mk_affinetable(sys.argv[1])

