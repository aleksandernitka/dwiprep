#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_acqparams(sid):
    
    import os
    import json
    from dipy.io.image import load_nifti

    """
    create acqparams.txt for topup
    0 1 0 TotalReadoutTime AP
    0 -1 0 TotalReadoutTime PA
    
    Number of lines depends on the number of volumes

    @author: aleksander nitka
    Created on Wed Apr 13 17:46:00 2022
    """
    
    # Load AP and PA b0s to establish number of volumes
    ap, __ = load_nifti(f'tmp/{sid}_AP_b0s.nii.gz')
    pa, __ = load_nifti(f'tmp/{sid}_PA_b0s.nii.gz')
    
    # Load JSONs
    apj = [f for f in os.listdir("tmp") if "_AP" in f and f.endswith("json")][0]
    paj = [f for f in os.listdir("tmp") if "_PA" in f and f.endswith("json")][0]


    with open(os.path.join("tmp", apj), "r") as f:
        json_ap = json.load(f)
        trt_ap = json_ap["TotalReadoutTime"]
        print(f"{sid} AP TotalReadoutTime: {trt_ap}")
        f.close()
        # write trt to file so it can be cat later
        with open(os.path.join("tmp", "trt_ap.txt"), "w") as t:
            t.write(str(trt_ap))
            t.close()

    with open(os.path.join("tmp", paj), "r") as f:
        json_pa = json.load(f)
        trt_pa = json_pa["TotalReadoutTime"]
        print(f"{sid} PA TotalReadoutTime: {trt_pa}")
        f.close()
        with open(os.path.join("tmp", "trt_pa.txt"), "w") as t:
            t.write(str(trt_pa))
            t.close()
    
    # Write acqparams file
    with open(os.path.join("tmp", "acqparams.txt"), "w") as f:
        for i in range(0, ap.shape[3]):
            #f.write(f"0 1 0 {trt_ap}\n0 -1 0 {trt_pa}")
            f.write(f"0 1 0 {trt_ap}\n")
        for j in range(0, pa.shape[3]):
            f.write(f"0 -1 0 {trt_pa}\n")
        
        f.close()


mk_acqparams(sys.argv[1])
