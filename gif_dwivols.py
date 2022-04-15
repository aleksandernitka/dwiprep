#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys


def gif_dwivols(sid):
    
    """
    plots all three views for each dwi vol into png, then makes a gif out of it. 
    Created on Fri Apr 15 09:58:08 2022

    @author: aleksander
    """
    
    import os
    import matplotlib.pyplot as plt
    from PIL import Image
    from dipy.io.image import load_nifti
    from shutil import rmtree

    dwi, aff = load_nifti(os.path.join('tmp', f'{sid}_AP.nii'))

    frames = []
    fdir = os.path.join('tmp', 'gif')
    if os.path.exists(fdir):
        rmtree(fdir)
    
    os.mkdir(fdir)
    
    for v in range(0, dwi.shape[3]):
        
        # plot all three sections
        fig1, ax = plt.subplots(1, 3, figsize=(16, 6), subplot_kw={'xticks': [], 'yticks': []})
        fig1.subplots_adjust(hspace=0.05, wspace=0.05)
        
        ax.flat[0].imshow(dwi[:,:,42,v].T, interpolation = 'none', origin = 'lower', cmap='hot')
        ax.flat[0].text(5,5, f'{v}', fontsize='large', c='red')
        ax.flat[1].imshow(dwi[:,50,:,v].T, interpolation = 'none', origin = 'lower', cmap='hot')
        ax.flat[2].imshow(dwi[50,:,:,v].T, interpolation = 'none', origin = 'lower', cmap='hot')
        fig1.savefig(os.path.join('tmp', 'gif', f'tmp_v_{v}.png'), bbox_inches='tight')
        
        # plt.imshow(dwi[:,:,42,v].T, interpolation = 'none', origin = 'lower', cmap='hot')
        # plt.axis('off')
        # plt.text(5,5, f'{v}', fontsize='large', c='red')
        # plt.savefig(os.path.join('tmp', 'gif', f'tmp_v_{v}.png'), bbox_inches='tight')
        # plt.close()
        
        new_frame = Image.open(os.path.join(fdir, f'tmp_v_{v}.png'))
        frames.append(new_frame)
        
    frames[0].save(os.path.join('tmp',f'{sid}_dwi_rawap.gif'), format='GIF',
               append_images=frames[1:],
               save_all=True,
               duration=300, loop=0)
    

    rmtree(fdir)
        
        

    
    
    


gif_dwivols(sys.argv[1])