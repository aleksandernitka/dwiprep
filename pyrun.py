#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 16:58:34 2022

@author: aleksander
"""

import subprocess as sb
import os

from nipype.interfaces.fsl import TOPUP
from nipype.interfaces.fsl.epi import ApplyTOPUP
from nipype.interfaces.fsl import Eddy
from nipype.interfaces.fsl import EddyQuad
'''
https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.epi.html
'''

hmridir = '/mnt/clab/COST_mri/derivatives/hMRI/'
subdir = '/mnt/clab/COST_mri/rawdata/'
tmpdir = '/home/aleksander/dwiprep/tmp2/'  # TODO change
outdir = '/mnt/clab/COST_mri/derivatives/dwipreproc/'
qaldir = '/mnt/clab/COST_mri/derivatives/quality/'

sid = 'sub-64742'

'''cmd_setup = 'source ~/.bashrc; '
cmd_topup = f'topup --imain=tmp/{sid}_AP-PA_b0s --datain=tmp/acqparams.txt --out=tmp/{sid}_AP-PA_topup -v --fout=tmp/{sid}_AP-PA_fout --iout=tmp/{sid}_AP-PA_iout --config=b02b0.cnf'

sb.call(cmd_setup + cmd_topup, shell= True)
'''

    topup = TOPUP()
    topup.inputs.in_file = "tmp_done/sub-64742_AP.nii"
    topup.inputs.encoding_file = os.path.join("tmp_done", "acqparams.txt")
    topup.inputs.output_type = "NIFTI_GZ"
    topup.out_corrected = os.path.join("tmp_done", f"{sid}_AP-PA_b0s_topup")
    topup.out_jacs = os.path.join("tmp_done", f"{sid}_AP-PA_b0s_topup_jacs")
    topup.out_movpar = os.path.join("tmp_done", f"{sid}_AP-PA_b0s_topup_movpar.txt")
    topup.out_warps = os.path.join("tmp_done", f"{sid}_AP-PA_b0s_topup_warps")
    topup.cmdline
#res = topup.run()
