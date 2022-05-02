#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from os import listdir as ls
from os import mkdir as mkd
from os.path import join
from random import sample
from shutil import copy
import subprocess as sb

p2sdir = '/mnt/clab/COST_mri/derivatives/dwi/preproc/'

# where the processed data is to be stored
store = '/mnt/clab/aleksander/experiments/data/denoise_compare/'


def compare_denoise(sid):
    """
    Compare the denoised data with the original data.
    

    Created on Thu Apr 21 15:20:57 2022
    @author: aleksander
    """

    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    import numpy as np
    import os
    from time import time
    import subprocess as sb

    # Import denoising algos
    from dipy.denoise.localpca import mppca
    from dipy.denoise.patch2self import patch2self
    from dipy.denoise.nlmeans import nlmeans
    from dipy.denoise.localpca import localpca
    
    # Import simple gaussian image blur
    from scipy.ndimage import gaussian_filter
    
    # Import noise estimates
    from dipy.denoise.noise_estimate import estimate_sigma
    from dipy.denoise.pca_noise_estimate import pca_noise_estimate
    
    # create or clear output dir
    tdir = 'denoise_test'
    if os.path.exists(tdir) == False:
        os.mkdir(tdir)
    
    # create ss output dir
    odir = os.path.join(tdir, sid)
    os.mkdir(odir)
    
    # Load all data
    dwi_ap, dwi_ap_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP.nii'))
    
    # load bval
    gt = gradient_table(os.path.join('tmp', sid, f'{sid}_AP.bval'), os.path.join('tmp', sid, f'{sid}_AP.bvec') )
    
    # noise estamate needs number of coils with which the data was acquired
    nCoils = 32
    sigma_base = estimate_sigma(dwi_ap, N=nCoils)
    np.save(os.path.join(odir, f'{sid}_sigma_base.npy'), sigma_base)
    
    # Denoise with gaussian blur
    def denoise_gauss(sid):
        t = time()
        print(f'{t} Started denoising with gaussian blur')
        den_gauss = dwi_ap.copy()
        for v in range(0, den_gauss.shape[3]):
            den_gauss[:,:,:,v] = gaussian_filter(den_gauss[:,:,:,v], sigma=0.5)
        sigma_gauss = estimate_sigma(den_gauss, N=nCoils)
        den_gauss_t = time() - t
        print(f'{time()} Completed denoising with gauss, it has taken {den_gauss_t}')
        # Save nii and noise params
        save_nifti(os.path.join(odir, f'{sid}_ap_gauss.nii.gz'), den_gauss, dwi_ap_affine)
        np.save(os.path.join(odir, f'{sid}_sigma_ap_gauss.npy'), sigma_gauss)
        
    
    # Denoise with non local means (nlm)
    # https://dipy.org/documentation/1.5.0/examples_built/denoise_nlmeans/#example-denoise-nlmeans
    def denoise_nlm(sid):
        t = time()
        print(f'{t} Started denoising with nlm')
        den_nlm = nlmeans(dwi_ap, sigma=sigma_base, mask=None, patch_radius=1, block_radius=2, rician=True, num_threads=-1)
        sigma_nlm = estimate_sigma(den_nlm, N=nCoils)
        den_nlm_t = time() - t
        print(f'{time()} Completed denoising with nlm, it has taken {den_nlm_t}')
        # Save nii and noise params
        save_nifti(os.path.join(odir, f'{sid}_ap_nlm.nii.gz'), den_nlm, dwi_ap_affine)
        np.save(os.path.join(odir, f'{sid}_sigma_ap_nlm.npy'), sigma_nlm)
        
    # Denoise with Marcenko-Pastur PCA
    # https://dipy.org/documentation/1.5.0/examples_built/denoise_mppca/#example-denoise-mppca
    def denoise_mppca(sid):
        t = time()
        print(f'{t} Started denoising with mppca')
        den_mppca = mppca(dwi_ap, patch_radius=3)
        sigma_mppca = estimate_sigma(den_mppca, N=nCoils)
        den_mppca_t = time() - t
        print(f'{time()} Completed denoising with mppca, it has taken {den_mppca_t}')
        # Save nii and noise params
        save_nifti(os.path.join(odir, f'{sid}_ap_mppca.nii.gz'), den_mppca, dwi_ap_affine)
        np.save(os.path.join(odir, f'{sid}_sigma_ap_mppca.npy'), sigma_mppca)
        
    # Denoise with local PCA
    # https://dipy.org/documentation/1.5.0/examples_built/denoise_localpca/#example-denoise-localpca
    def denoise_lpca(sid):
        t = time()
        print(f'{t} Started denoising with local PCA')
        sigma_pca_pre = pca_noise_estimate(dwi_ap, gt, correct_bias=True, smooth=3) # this method is unique to lpca
        den_lpca = localpca(dwi_ap, sigma_pca_pre, tau_factor=2.3, patch_radius=3)
        sigma_pca_post = pca_noise_estimate(den_lpca, gt, correct_bias=True, smooth=3)
        sigma_lpca = estimate_sigma(den_lpca, N=nCoils)
        den_lpca_t = time() - t
        print(f'{time()} Completed denoising with lpca, it has taken {den_lpca_t}')
        # Save nii and noise params
        save_nifti(os.path.join(odir, f'{sid}_ap_lpca.nii.gz'), den_lpca, dwi_ap_affine)
        np.save(os.path.join(odir, f'{sid}_sigmaPca_ap_lpca_pre.npy'), sigma_pca_pre)
        np.save(os.path.join(odir, f'{sid}_sigmaPca_ap_lpca_post.npy'), sigma_pca_post)
        np.save(os.path.join(odir, f'{sid}_sigma_ap_lpca.npy'), sigma_lpca)
        
    # Denoise with patch2self
    def denoise_p2s(sid):
        t=time()
        print(f'{t} Started denoising with patch2self')
        den_p2s = patch2self(dwi_ap, gt.bvals)
        sigma_p2s = estimate_sigma(den_p2s, N=nCoils)
        den_p2s_t = time() - t
        print(f'{time()} Completed denoising with patch2self, it has taken {den_p2s_t}')
        # Save nii and noise params
        save_nifti(os.path.join(odir, f'{sid}_ap_p2s.nii.gz'), den_p2s, dwi_ap_affine)
        np.save(os.path.join(odir, f'{sid}_sigma_p2s.npy'), sigma_p2s)
    
    def denoise_mrtrix(sid):
        t = time()
        print(f'{t} Started denoising with mrtrix mppca')
        f_nii = os.path.join('tmp', sid,  f'{sid}_AP.nii')
        f_den = os.path.join(odir, f'{sid}_ap_mrtrix.nii.gz')
        f_noi = os.path.join(odir, f'{sid}_ap_mrtrix_noise.nii.gz')
        f_res = os.path.join(odir, f'{sid}_ap_mrtrix_resid.nii.gz')
        sb.run(f'dwidenoise {f_nii} {f_den} -noise {f_noi}', shell = True)
        sb.run(f'mrcalc {f_nii} {f_den} -subtract {f_res}', shell = True)
        den_mrtrix_t = time()-t
        print(f'{time()} Completed denoising with mrtrix, it has taken {den_mrtrix_t}')
        # load nii
        nii, __ = load_nifti(os.path.join(odir, f'{sid}_ap_mrtrix.nii.gz'))
        sigma_mrtrix = estimate_sigma(nii, N=nCoils)
        # save sigma
        np.save(os.path.join(odir, f'{sid}_sigma_mrtrix.npy'), sigma_mrtrix)
    
    # run functions:
    denoise_gauss(sid=sid)
    denoise_nlm(sid=sid)
    denoise_mppca(sid=sid)
    denoise_lpca(sid=sid)
    denoise_mrtrix(sid=sid)
    # denoise_p2s(sid=sid)
    
    # Save gradients
    np.save(os.path.join(odir, f'{sid}_bvals.npy'), gt.bvals)

subs = [f for f in ls(p2sdir) if f.startswith('sub-')]

samp = sample(subs, 25)

for i, s in enumerate(samp):
    
    print(f'{s} {i+1} processing')
        
    mkd(join('tmp', s))

    copy(join(p2sdir, s, f'{s}_AP.nii'), join('tmp', s, f'{s}_AP.nii'))
    copy(join(p2sdir, s, f'{s}_AP.bval'), join('tmp', s, f'{s}_AP.bval'))
    copy(join(p2sdir, s, f'{s}_AP.bvec'), join('tmp', s, f'{s}_AP.bvec'))
    copy(join(p2sdir, s, f'{s}_AP_denoised.nii.gz'), join('tmp', s, f'{s}_AP_denoised.nii.gz'))
    copy(join(p2sdir, s, f'{s}_AP_sigma_noise_p2s.npy'), join('tmp', s, f'{s}_AP_sigma_noise_p2s.npy'))
    
    compare_denoise(s)
    
    sb.run(f'cp tmp/{s}/* denoise_test/{s}/', shell=True)
    sb.run(f'cp -r denoise_test/{s} {store}/', shell=True) 
    
    sb.run(f'rm -rf tmp/{s}', shell=True)
    sb.run(f'rm -rf denoise_test/{s}', shell=True)


    

