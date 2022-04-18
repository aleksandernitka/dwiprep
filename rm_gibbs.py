#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys

def rm_gibbs(sid, fap, fpa):
    
    """
    Noting fancy, just running the gibbs removal algo from DIPY, then saving the output as well as pngs for qa.
    
    Created on Fri Apr 15 14:51:09 2022

    @author: admin
    """

    from dipy.denoise.gibbs import gibbs_removal
    from dipy.io.image import load_nifti, save_nifti
    import matplotlib.pyplot as plt
    from shutil import rmtree as rmt
    from datetime import datetime as dt
    import os
    
    
    # Load dwi
    dwi_ap, dwi_affine_ap = load_nifti(os.path.join('tmp', fap))
    dwi_pa, dwi_affine_pa = load_nifti(os.path.join('tmp', fpa))
    
    # degibbs dwi
    dwi_ap_dg = gibbs_removal(dwi_ap, inplace=False, num_processes=-1)
    dwi_pa_dg = gibbs_removal(dwi_pa, inplace=False, num_processes=-1)
    
    # Plot all volumes
    s = 42 # slice
    png_dir = os.path.join('tmp', f'{sid}_gibbs_pngs')
    
    if os.path.exists(png_dir):
        rmt(png_dir)
        os.mkdir(png_dir)
    else:
        os.mkdir(png_dir)
        
    html = f"<!DOCTYPE html><HTML><body><center><h1>{sid}</h1><br><p>Denoising was \
        performed with DIPY (v1.5.0) gibbs_removal with default settings, aside from number of processes set to max available.\
                    </p><br><a href='#pa'>Jump to PA</a><br><h2 id = 'ap'>AP Volumes</h2><br><br>"
    
    # plots AP
    for i in range(0, dwi_ap_dg.shape[3]):
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
        fig1.title(f'{sid} AP vol={i}', fontsize = 15)
        
        ax.flat[0].imshow(dwi_ap[:, :, s, i].T, cmap='gray', origin='lower',vmin=0, vmax=10000)
        ax.flat[0].set_title(f'Uncorrected b0 {i}')
        
        ax.flat[1].imshow(dwi_ap_dg[:, :, s, 0].T, cmap='gray', origin='lower', vmin=0, vmax=10000)
        ax.flat[1].set_title('Corrected b0')
        
        ax.flat[2].imshow(dwi_ap_dg[:, :, s, 0].T - dwi_ap[:, :, 4, 0].T,cmap='gray', origin='lower', vmin=-500, vmax=500)
        ax.flat[2].set_title('Gibbs residuals')
        
        plt.show()
        fig1.savefig(os.path.join(png_dir, f'{sid}_gibbs_ap_{i}.png'))
        
        # Add to html
        html += f'<img src="{sid}_gibbs_pngs/{sid}_gibbs_ap_{i}.png"><br>'
        
    html+="<br><br><h2 id = 'pa'>PA Volumes</h2><br><br>"
    
    # plots AP
    for i in range(0, dwi_pa_dg.shape[3]):
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
        
        ax.flat[0].imshow(dwi_pa[:, :, s, i].T, cmap='gray', origin='lower',vmin=0, vmax=10000)
        ax.flat[0].set_title(f'Uncorrected b0 {i}')
        
        ax.flat[1].imshow(dwi_pa_dg[:, :, s, 0].T, cmap='gray', origin='lower', vmin=0, vmax=10000)
        ax.flat[1].set_title('Corrected b0')
        
        ax.flat[2].imshow(dwi_pa_dg[:, :, s, 0].T - dwi_pa[:, :, 4, 0].T,cmap='gray', origin='lower', vmin=-500, vmax=500)
        ax.flat[2].set_title('Gibbs residuals')
        
        plt.show()
        fig1.savefig(os.path.join(png_dir, f'{sid}_gibbs_pa_{i}.png'))
        # Add to html
        html += f'<img src="{sid}_gibbs_pngs/{sid}_gibbs_pa_{i}.png"><br>'
    
    # Save niis
    save_nifti(os.path.join('tmp', f'{sid}_AP_degibbs.nii.gz'), dwi_ap_dg, dwi_affine_ap)
    save_nifti(os.path.join('tmp', f'{sid}_PA_degibbs.nii.gz'), dwi_pa_dg, dwi_affine_pa)
    
    # close html
    html += f'Produced by machines of superior intelligence under the guidiance \
        from their fearless leader and commander Aleksander on {dt.now()} </center></body></HTML>'
    # save html
    with open(os.path.join('tmp', f'{sid}_degibbs.html'), 'w') as h:
        h.write(html)
        h.close()

rm_gibbs(sys.argv[1], sys.argv[2], sys.argv[3])