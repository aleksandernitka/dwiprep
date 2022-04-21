#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def compare_denoise(sid):
    
    """
    Compare multiple denoising strategies using dipy 1.5.0 provided algos
    Assumes AP, bval, bvec data in 'tmp' dir. 
    
    Created on Thu Apr 21 15:20:57 2022
    @author: aleksander
    """

    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    from dipy.core.histeq import histeq
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from time import time
    import cmocean
    from shutil import rmtree as rmt
    import pickle 
    
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
    else:
        rmt(tdir)
        os.mkdir(tdir)
        
    # create ss output dir
    odir = os.path.join(tdir, sid)
    os.mkdir(odir)
    
    # Load all data
    dwi_ap, dwi_ap_affine = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))
    
    # load bval
    gt = gradient_table(os.path.join('tmp', f'{sid}_AP.bval'), os.path.join('tmp', f'{sid}_AP.bvec') )
    
    # noise estamate needs number of coils with which the data was acquired
    nCoils = 32
    sigma_base = estimate_sigma(dwi_ap, N=nCoils)
    np.save(os.path.join(odir, f'{sid}_sigma_base.npy'), sigma_base)
    
    # Denoise with gaussian blur
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
    t = time()
    print(f'{t} Started denoising with local PCA')
    sigma_pca_pre = pca_noise_estimate(dwi_ap, gt, correct_bias=True, smooth=3) # this method is unique to lpca
    den_lpca = localpca(dwi_ap, sigma_pca_pre, tau_factor=2.3, patch_radius=2)
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
    t=time()
    print(f'{t} Started denoising with patch2self')
    den_p2s = patch2self(dwi_ap, gt.bvals)
    sigma_p2s = estimate_sigma(den_p2s, N=nCoils)
    den_p2s_t = time() - t
    print(f'{time()} Completed denoising with patch2self, it has taken {den_p2s_t}')
    # Save nii and noise params
    save_nifti(os.path.join(odir, f'{sid}_ap_p2s.nii.gz'), den_p2s, dwi_ap_affine)
    np.save(os.path.join(odir, f'{sid}_sigma_p2s.npy'), sigma_p2s)
    
    # Save raw image
    save_nifti(os.path.join(odir, f'{sid}_AP.nii.gz'), dwi_ap, dwi_ap_affine)
    # save gradtable
    pickle.dump(gt, os.path.join(odir, f'{sid}_gt.obj'))