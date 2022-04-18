#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def mk_gradients(sid, bvals, bvecs):
    
    """
    Input bval, bvecs and dipy will create gradinent table, produce a bvals
    histogram to file as well as plot gradients on a sphere
    
    Function returns:
    b0 mask - which volumes are b0 in the AP data, this is saved as a npy file in tmp
    bvals plot - distribution of gradients (for QA)
    gradients plot - spehere showing all bvals and bvecs plotted as a sphere
    gradients txt - a txt file with information about gradients - for QA html
    
    
    Created on Mon Apr 18 19:45:31 2022

    @author: aleksander nitka
    """

    from dipy.core.gradients import gradient_table
    from dipy.io.gradients import read_bvals_bvecs
    from dipy.viz import window, actor
    
    import numpy as np
    import matplotlib.pyplot as plt
    
    gt_bvals, gt_bvecs = read_bvals_bvecs(bvals, bvecs)
    
    gtab = gradient_table(bvals, bvecs)
    
    # make text for html
    txt = f'bvals shape {gt_bvals.shape}, min = {gt_bvals.min()}, max = {gt_bvals.max()}\
        with {len(np.unique(gtab.bvals))} unique values: {np.unique(gtab.bvals)}\
        bvecs shape {gt_bvecs.shape}, min = {gt_bvecs.min()}, max = {gt_bvecs.max()}'

    with open(f'tmp/{sid}_gradients.txt', 'w') as f:
        f.wite(txt)
        f.close()
        
        
    # plot hist of b-vals 
    plt.hist(gtab.bvals, bins = len(np.unique(gtab.bvals)), label=f'{sid} bvals')
    plt.savefig(f'tmp/{sid}_bvals.png')
    plt.close()
    
    # Make a nice plot with all gtab data
    interactive = False
    
    scene = window.Scene()
    scene.SetBackground(1, 1, 1)
    scene.clear()
    scene.add(actor.point(gtab.gradients, window.colors.red, point_radius=100))
    window.record(scene, out_path=f'tmp/{sid}_gradients.png', size=(600, 600))
    
    if interactive:
        window.show(scene)

    # save b0s mask as numpy array  - which volumes are b0 in AP (bool)
    np.save(f'tmp/{sid}_b0mask.npy', gtab.b0s_mask)
    
mk_gradients(sys.argv[1], sys.argv[2], sys.argv[3])