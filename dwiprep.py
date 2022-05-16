#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def mk_run_lists_pretopup(rawdir, list_len):
    """
    Because fsl's topup is not paralelised, to speed things up, it would be beneficial
    if things are run concurently using multiple proccessing lists. This fn creates
    N-number of lists of all but last one are of specified len. 

    Parameters
    ----------
    rawdir : PATH or STR
        Location of rawdata to source sub-ids.
        
    list_len : INT
        How long shall each list be.

    Returns
    -------
    Saves X runList_x.csv files in the root dir.
    
    Created on Fri Apr 22 10:37:14 2022
    @author: aleksander nitka

    """

    import os
    from itertools import islice
    
    subs = [f for f in os.listdir(rawdir) if f.startswith('sub-')]

    # each list shall be of len:
    list_len = 2
    # list to hold required lens for each list
    lens = []
    # keep the tally up
    totaln = len(subs)
    
    # add list len untill len is less than the list len
    while totaln > list_len:
        lens.append(list_len)
        totaln = totaln - list_len
    lens.append(totaln)
    totaln = totaln - totaln  # Should 0
    
    # this should generate list of lists
    it = iter(subs)
    outputs = [list(islice(it, elem)) for elem in lens]
    
    # for each sub-list write a file
    for i, l in enumerate(outputs):
        with open(f'runList_{i}.csv', 'w') as f:
            # each subjects needs to be written to a file
            for j in outputs[i]:
                f.write(f'{j}\n')
            f.close()


def run_topup(sid):
    """
    DEPRECATED

    Using subprocess this fn runs the fsl topup. Noting more nothing less. 

    Parameters
    ----------
    sid : STR
        Subject id with 'sub' prefix.

    Returns
    -------
    - Standard topup outputs, including fout and iout

    """
    import subprocess as sb
    
    # note the config file copied from /usr/local/fsl/etc/flirtsch/b02b0.cnf
    
    tp_cmd = f'topup --config=b02b0.cnf --datain=tmp/{sid}/acqparams.txt \
        --imain=tmp/{sid}/{sid}_AP-PA_b0s.nii.gz --out=tmp/{sid}/{sid}_AP-PA_topup \
        --iout=tmp/{sid}/{sid}_iout --fout=tmp/{sid}/{sid}_fout -v \
        --jacout=tmp/{sid}/{sid}_jac --logout=tmp/{sid}/{sid}_topup.log \
        --rbmout=tmp/{sid}/{sid}_xfm --dfout=tmp/{sid}/{sid}_warpfield'
    
    sb.run(tp_cmd, shell=True)

def mk_bet_brain_mask(sid):
    """
    Runs BET brain extraction and mask algo. Bet here is run twice;
    once with no parameters and once with estimation of center mass of the brain

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.

    Returns
    -------
    - Binary mask
    - Extracted brain image

    """

    from subprocess import run
    
    img = f'tmp/{sid}/{sid}_iout_mean'
    
    # run center of mass estimation for bet2_2
    # Find center of mass of the image.
    com = f'fslstats {img} -C'
    # Run the command.
    com_result = run(com, capture_output=True, shell=True)
    
    # run bet and bet2 in bash
    cmd_bet2_1 = f'bet2 tmp/{sid}/{sid}_iout_mean tmp/{sid}/{sid}_iout_bet2 -m -o'
    cmd_bet2_2 = f'bet2 tmp/{sid}/{sid}_iout_mean tmp/{sid}/{sid}_iout_bet2c -m -o -c {com_result.stdout.decode}'
    run(cmd_bet2_1, shell=True)
    run(cmd_bet2_2, shell=True)
    
def mk_otsu_brain_mask(sid):
    """
    BET generated brain mask is not too good and often comes significantly eroded
    with regards to the dwi brain. The OTSU method from DIPY seems to do a 
    better job (in some cases), but it is recomended to check anyhow. 

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.

    Returns
    -------
    - Bianry brain mask
    - Extracted brain image
    """
    
    import os
    from dipy.segment.mask import median_otsu
    from dipy.io.image import load_nifti, save_nifti

    import numpy as np
    
    b0, b0_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_iout_mean.nii.gz'))
    
    # Make mask with median_otsu method, default params
    b0_mask, mask = median_otsu(b0)
    
    # save to nifti
    save_nifti(os.path.join('tmp', sid, f'{sid}_iout_otsu.nii.gz'), b0_mask, b0_affine)
    save_nifti(os.path.join('tmp', sid, f'{sid}_iout_otsu_mask.nii.gz'), mask.astype(np.float32), b0_affine)
    
def comp_masks(sid):
    
    """
    Should be run after both mk_otsu_brain_mask and mk_bet_brain_mask were run
    this fn plots the three against each other for comparison
    Generates one image for QA.
    """
    
    from nilearn import plotting
    import matplotlib.pyplot as plt
    from os.path import join
    from matplotlib.patches import Rectangle
    
    p_b2 = join('tmp', sid, f'{sid}_iout_bet2_mask.nii.gz')
    p_b2c = join('tmp', sid, f'{sid}_iout_bet2c_mask.nii.gz')
    p_otsu = join('tmp', sid, f'{sid}_iout_otsu_mask.nii.gz')
    p_img = join('tmp', sid, f'{sid}_iout_mean.nii.gz')
    
    a = .3 # alpha
    l = 2 # line
    fig = plt.figure(figsize=(12, 5))
    # plot with nilearn
    display = plotting.plot_anat(p_img, cut_coords = (0, 0, 50), display_mode='ortho', cmap='gray', draw_cross = 0, figure = fig, title = f'{sid}')
    display.add_contours(p_b2, alpha = a, antialiased=1, linewidths=l, colors=['red'], filled = 0)
    display.add_contours(p_b2c, alpha = a, antialiased=1, linewidths=l, colors=['blue'], filled = 0)
    display.add_contours(p_otsu, alpha = a, antialiased=1, linewidths=l, colors=['green'], filled = 0)
    display.annotate(scalebar=True)
    
    bet2 = Rectangle((0, 0), 1, 1, fc="red")
    bet2c = Rectangle((0, 0), 1, 1, fc="blue")
    otsu = Rectangle((0, 0), 1, 1, fc="green")
    plt.legend([bet2, bet2c, otsu], ["BET2", "BET2+c", "OTSU"])

    display.savefig(f'tmp/{sid}/{sid}_MSKQA.png')
    display.close()

def mk_index_eddy(sid):
    """
    Creates index for Eddy.

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.

    Returns
    -------
    - index file: eddyindex.txt

    """
    
    import os
    from dipy.io.image import load_nifti
    
    dwi, __ = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_denoised.nii.gz'))
    vols = dwi.shape[3]
    
    #print(f'{sid} {vols} detected')
    
    with open(os.path.join('tmp', sid, 'eddyindex.txt'), 'w') as i:
        for l in range(1, vols+1):
            i.write('1 ')
    i.close()
    
   
def mk_b0s(sid):
    """
    Extracts all b0s from the AP.nii and saves it as AP_b0s.nii.gz
    For the other direction it only plots and saves it for consistency
    Control plot with all b0s is saved as AP_b0s.png
    
    Created on Tue Apr 19 10:27:49 2022
    @author: aleksander nitka
    """
    
    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    import matplotlib.pyplot as plt
    import os
    
    gtab = gradient_table(f'tmp/{sid}/{sid}_AP.bval', f'tmp/{sid}/{sid}_AP.bvec')
    
    dwi_ap, affine_ap = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_denoised.nii.gz'))
    dwi_pa, affine_pa = load_nifti(os.path.join('tmp', sid, f'{sid}_PA_denoised.nii.gz'))
    
    b0s_ap = dwi_ap[:,:,:,gtab.b0s_mask]
    b0s_pa = dwi_pa[:,:,:,[True, True, True, True, True]]
    
    # Control figure AP
    fig1, ax = plt.subplots(2, 5, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    fig1.suptitle(f'{sid} AP b0s', fontsize = 20)
    
    for i in range(0, b0s_ap.shape[3]):
        
        ax.flat[i].imshow(b0s_ap[:,:,42,i].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[i].set_title(f'{i}')
        
    fig1.savefig(os.path.join('tmp', sid, f'{sid}_AP_b0s.png'))
    
    # Control figure PA
    fig1, ax = plt.subplots(1, 5, figsize=(12, 3),subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.15)
    fig1.suptitle(f'{sid} PA b0s', fontsize = 20)
    
    for i in range(0, b0s_pa.shape[3]):
        
        ax.flat[i].imshow(b0s_pa[:,:,42,i].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[i].set_title(f'{i}')
        
    fig1.savefig(os.path.join('tmp', sid, f'{sid}_PA_b0s.png'))
    
    # Save AP b0s
    save_nifti(f'tmp/{sid}/{sid}_AP_b0s.nii.gz', b0s_ap, affine_ap)   
    save_nifti(f'tmp/{sid}/{sid}_PA_b0s.nii.gz', b0s_pa, affine_pa)  
    
def mk_acq_params(sid):
    """
    create acqparams.txt for topup
    0 1 0 TotalReadoutTime AP
    0 -1 0 TotalReadoutTime PA
    
    Number of lines depends on the number of volumes

    @author: aleksander nitka
    Created on Wed Apr 13 17:46:00 2022
    """
    
    import os
    import json
    from dipy.io.image import load_nifti
    
    # Load AP and PA b0s to establish number of volumes
    ap, __ = load_nifti(f'tmp/{sid}/{sid}_AP_b0s.nii.gz')
    pa, __ = load_nifti(f'tmp/{sid}/{sid}_PA_b0s.nii.gz')
    
    # Load JSONs
    apj = [f for f in os.listdir(f"tmp/{sid}/") if "_AP" in f and f.endswith("json")][0]
    paj = [f for f in os.listdir(f"tmp/{sid}/") if "_PA" in f and f.endswith("json")][0]

    # TODO make one function for both
    with open(os.path.join("tmp", sid, apj), "r") as f:
        json_ap = json.load(f)
        trt_ap = json_ap["TotalReadoutTime"]
        print(f"{sid} AP TotalReadoutTime: {trt_ap}")
        f.close()
        # write trt to file so it can be cat later
        with open(os.path.join("tmp", sid, "trt_ap.txt"), "w") as t:
            t.write(str(trt_ap))
            t.close()

    with open(os.path.join("tmp", sid, paj), "r") as f:
        json_pa = json.load(f)
        trt_pa = json_pa["TotalReadoutTime"]
        print(f"{sid} PA TotalReadoutTime: {trt_pa}")
        f.close()
        with open(os.path.join("tmp", sid, "trt_pa.txt"), "w") as t:
            t.write(str(trt_pa))
            t.close()
    
    # Write acqparams file
    with open(os.path.join("tmp", sid, "acqparams.txt"), "w") as f:
        for i in range(0, ap.shape[3]):
            #f.write(f"0 1 0 {trt_ap}\n0 -1 0 {trt_pa}")
            f.write(f"0 1 0 {trt_ap}\n")
        for j in range(0, pa.shape[3]):
            f.write(f"0 -1 0 {trt_pa}\n")
        
        f.close()
        
def rm_noise_p2s(sid):
    
    """
    Uses dipy's patch2self to denoise the dwi image, relies on scikit-klearn so install that first.
    After processing the AP volume (around 3h on Macbook Pro 2017) it will process PA 
    with bvals set as [5,5,5,5,5].Then it procuces a control plots for all volumes in both sets.
    Saves both as sub-xxxx_AP_denoised in tmp. Creates html page for all pngs created (QA)


    Created on Fri Apr 15 15:20:23 2022
    @author: aleksander nitka
    """
    
    from dipy.io.image import load_nifti, save_nifti
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from shutil import rmtree as rmt
    from dipy.denoise.patch2self import patch2self
    from datetime import datetime as dt
    from dipy.core.histeq import histeq
    from dipy.denoise.noise_estimate import estimate_sigma
    
    xcmp = 'gray'
    
    # Number of coils used in scan
    nC = 32
    
    # Load dwi
    dwi_ap, dwi_ap_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP.nii'))
    dwi_pa, dwi_pa_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_PA.nii'))
    
    # load bval
    bvals_ap = np.loadtxt(os.path.join('tmp', sid, f'{sid}_AP.bval'))
    bvals_pa = np.array([5.,5.,5.,5.,5.])
    
    # Calculate noise standaard deviation for raw data
    sigma_ap_raw = estimate_sigma(dwi_ap, N = nC)
    sigma_pa_raw = estimate_sigma(dwi_pa, N = nC)
    
    # Process AP
    dwi_ap_den = patch2self(dwi_ap, bvals_ap, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)
    # calculate sigma of noise
    sigma_ap_den = estimate_sigma(dwi_ap_den, N = nC)
    # Save NII
    save_nifti(os.path.join('tmp', sid, f'{sid}_AP_denoised.nii.gz'), dwi_ap_den, dwi_ap_affine)
    
    # Process PA
    dwi_pa_den = patch2self(dwi_pa, bvals_pa, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)
    # calculate sigma of noise
    sigma_pa_den = estimate_sigma(dwi_pa_den, N = nC)
    # Save NII
    save_nifti(os.path.join('tmp', sid, f'{sid}_PA_denoised.nii.gz'), dwi_pa_den, dwi_pa_affine)
    
    # Save noise estimates
    np.save(f'tmp/{sid}/{sid}_AP_sigma_noise_raw.npy', sigma_ap_raw)
    np.save(f'tmp/{sid}/{sid}_PA_sigma_noise_raw.npy', sigma_pa_raw)
    np.save(f'tmp/{sid}/{sid}_AP_sigma_noise_p2s.npy', sigma_ap_den)
    np.save(f'tmp/{sid}/{sid}_PA_sigma_noise_p2s.npy', sigma_pa_den)
    
    # Plot all volumes
    s = 42 # slice
    png_dir = os.path.join('tmp', sid, f'{sid}_p2s_pngs')
    
    if os.path.exists(png_dir):
        rmt(png_dir)
        os.mkdir(png_dir)
    else:
        os.mkdir(png_dir)
    
    html = f"<!DOCTYPE html><HTML><body><center><h1>{sid}</h1><br><p>Denoising was \
        performed with Python 3.6 and DIPY (v1.5.0) patch2self tool (it relied on scikit-learn v1.0.2) \
            with model set as ordinary least squares ‘ols’, b0 threshold set at 50, \
                intensity shifting and negative values clipping enabled.\
                    </p><br><a href='#pa'>Jump to PA</a><br><h2 id = 'ap'>AP Volumes</h2><br><br>"
    
    def plt_denoised(raw, den, direction, sigma_raw, sigma_den, html_file):
        # TODO finish this fn
        """
        Creates control plots after denoisings procedure has been completed

        Parameters
        ----------
        raw : TYPE
            DESCRIPTION.
        den : TYPE
            DESCRIPTION.
        direction : TYPE
            DESCRIPTION.
        sigma_raw : TYPE
            DESCRIPTION.
        sigma_den : TYPE
            DESCRIPTION.
        html_file : TYPE
            DESCRITOPN.

        Returns
        -------
        None.

        """
    
    # plots for AP
    for i, vs in enumerate(range(0, dwi_ap_den.shape[3])):
    
    
        # computes the residuals
        rms_diff = np.sqrt(abs((dwi_ap[:,:,s,vs] - dwi_ap_den[:,:,s,vs]) ** 2))
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    
        fig1.subplots_adjust(hspace=0.05, wspace=0.05)
        fig1.suptitle(f'{sid} AP vol={vs} bval={int(bvals_ap[i])}', fontsize =20)
    
        ax.flat[0].imshow(dwi_ap[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
        ax.flat[0].set_title('Original, ' + r'$\sigma_{noise}$' + f' = {round(sigma_ap_raw[i])}')
        ax.flat[1].imshow(dwi_ap_den[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
        ax.flat[1].set_title('Denoised, ' + r'$\sigma_{noise}$' + f' = {round(sigma_ap_den[i])}')
        ax.flat[2].imshow(rms_diff.T, cmap=xcmp, interpolation='none',origin='lower')
        ax.flat[2].set_title('Residuals')
        
        sfig = os.path.join(png_dir, f'{sid}_ap_bv-{int(bvals_ap[i])}_v-{vs}.png')
        hfig = os.path.join(f'{sid}_p2s_pngs', f'{sid}_ap_bv-{int(bvals_ap[i])}_v-{vs}.png')
        fig1.savefig(sfig)
        
        # Add to html
        html += f'<img src="{hfig}"><br>'
        plt.close()
    
    html+="<br><br><h2 id = 'pa'>PA Volumes</h2><br><br><p>Please note that PA volumes were denoised assuming five b-vals of 5.<br><br>"
    
    # Plots for PA
    # FIX make one function to make both plot types
    for i, vs in enumerate(range(0, dwi_pa_den.shape[3])):
    
        # computes the residuals
        rms_diff = np.sqrt(abs(dwi_pa[:,:,s,vs] - dwi_pa_den[:,:,s,vs]) ** 2)
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    
        fig1.subplots_adjust(hspace=0.05, wspace=0.05)
        fig1.suptitle(f'{sid} PA vol={vs} bval={int(bvals_pa[i])}', fontsize=20)
    
        ax.flat[0].imshow(dwi_pa[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
        ax.flat[0].set_title(f'Original, ' + r'$\sigma_{noise}$' + f' = {round(sigma_pa_raw[i])}')
        ax.flat[1].imshow(dwi_pa_den[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
        ax.flat[1].set_title('Denoised, ' + r'$\sigma_{noise}$' + f' = {round(sigma_pa_den[i])}')
        ax.flat[2].imshow(rms_diff.T, cmap=xcmp, interpolation='none', origin='lower')
        ax.flat[2].set_title('Residuals')
    
        sfig = os.path.join(png_dir, f'{sid}_pa_bv-{int(bvals_pa[i])}_v-{vs}.png')
        hfig = os.path.join(f'{sid}_p2s_pngs', f'{sid}_pa_bv-{int(bvals_pa[i])}_v-{vs}.png')
        fig1.savefig(sfig)
        
        # Add to html
        html += f'<img src="{hfig}"><br>'
        plt.close() 
    
    
    
    # close html
    html += f'Produced by machines of superior intelligence under the guidiance \
        from their fearless leader and commander Aleksander on {dt.now()} </center></body></HTML>'
    # save html
    with open(os.path.join('tmp', sid, f'{sid}_p2s_denoise.html'), 'w') as h:
        h.write(html)
        h.close()
        
def rm_gibbs(sid, fap, fpa):
    
    """
    Noting fancy, just running the gibbs removal algo from DIPY, then saving the
    output as well as pngs for qa.
    
    Created on Fri Apr 15 14:51:09 2022
    @author: aleksander nitka
    """

    from dipy.denoise.gibbs import gibbs_removal
    from dipy.io.image import load_nifti, save_nifti
    import matplotlib.pyplot as plt
    from shutil import rmtree as rmt
    from datetime import datetime as dt
    import os
    
    
    # Load dwi
    dwi_ap, dwi_affine_ap = load_nifti(os.path.join('tmp', sid, fap))
    dwi_pa, dwi_affine_pa = load_nifti(os.path.join('tmp', sid, fpa))
    
    # degibbs dwi
    dwi_ap_dg = gibbs_removal(dwi_ap, inplace=False, num_processes=-1)
    dwi_pa_dg = gibbs_removal(dwi_pa, inplace=False, num_processes=-1)
    
    # Plot all volumes
    s = 42 # slice
    png_dir = os.path.join('tmp', sid, f'{sid}_gibbs_pngs')
    
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
    save_nifti(os.path.join('tmp', sid, f'{sid}_AP_degibbs.nii.gz'), dwi_ap_dg, dwi_affine_ap)
    save_nifti(os.path.join('tmp', sid, f'{sid}_PA_degibbs.nii.gz'), dwi_pa_dg, dwi_affine_pa)
    
    # close html
    html += f'Produced by machines of superior intelligence under the guidiance \
        from their fearless leader and commander Aleksander on {dt.now()} </center></body></HTML>'
    # save html
    with open(os.path.join('tmp', sid, f'{sid}_degibbs.html'), 'w') as h:
        h.write(html)
        h.close()
        
def mk_gradients(sid):
    
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
    #from dipy.viz import window, actor
    import numpy as np
    import matplotlib.pyplot as plt
    
    gtab = gradient_table(f'tmp/{sid}/{sid}_AP.bval', f'tmp/{sid}/{sid}_AP.bvec')
    
    # make text for html
    txt = f'bvals shape {gtab.bvals.shape}, min = {gtab.bvals.min()}, max = {gtab.bvals.max()} with {len(np.unique(gtab.bvals))} unique values: {np.unique(gtab.bvals)}bvecs shape {gtab.bvecs.shape}, min = {gtab.bvecs.min()}, max = {gtab.bvecs.max()}'

    with open(f'tmp/{sid}/{sid}_gradients.txt', 'w') as f:
        f.write(txt)
        f.close()
        
        
    # plot hist of b-vals 
    plt.hist(gtab.bvals, bins = len(np.unique(gtab.bvals)), label=f'{sid} bvals')
    plt.savefig(f'tmp/{sid}/{sid}_bvals.png')
    plt.close()
    
    # Make a nice plot with all gtab data
    # Unable to plot this onb KPC - crashes kernel
    # interactive = False
    
    # scene = window.Scene()
    # scene.SetBackground(1, 1, 1)
    # scene.clear()
    # scene.add(actor.point(gtab.gradients, window.colors.red, point_radius=100))
    # window.record(scene, out_path=f'tmp/{sid}_gradients.png', size=(600, 600))
    
    # if interactive:
    #     window.show(scene)

    # save b0s mask as numpy array  - which volumes are b0 in AP (bool)
    np.save(f'tmp/{sid}/{sid}_b0mask.npy', gtab.b0s_mask)
     
def cp_dwi_files(sid, rawdata, where):
    
    """
    Copy all files needed for preprocessing in dwi, make sure all dirs exist

    Created on Wed Apr 13 17:46:00 2022
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


def plt_topup_outlines(s):
    """
    Plot the outlines of the topup images and AP, PA.
    
    RUN with plt_topup function

    Adapted from the flywheel code, but with plotting from nilearn.
    source: https://github.com/flywheel-apps/fsl-topup/blob/master/mri_qa.py
    """
    
    from os import remove as rm
    from subprocess import run
    from nilearn import plotting
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    # First extract first volume from each image, in second run take the mean image
    pth = f'tmp/{s}/{s}'
    b0s_x = ['_AP_b0s', '_PA_b0s', '_iout']
        
    b0s_y = ['_TPQA_AP_b01', '_TPQA_PA_b01', '_TPQA_TP_b01', \
             '_AP_b0s_mean', '_PA_b0s_mean', '_iout_mean']
        
    for j, x in enumerate(b0s_x):
        # extract first volume of b0s
        cmd = f'fslroi {pth}{x} {pth}{b0s_y[j]} 0 1'
        run(cmd, shell=True)

    # Run bet on ap, pa and topup images.
    for i in b0s_y:
        
        img = f'{pth}{i}'

        # Find center of mass of the image.
        com = f'fslstats {img} -C'
        # Run the command.
        com_result = run(com, capture_output=True, shell=True)

        # Run bet2 on the image.
        # cmd = f'bet2 {img} {img}_brain -o -m -t -f 0.5 -w 0.4 -c {com_result.stdout.decode()}'
        cmd = f'bet2 {img} {img}_b -m -w 1.1 -c {com_result.stdout.decode()}'
        run(cmd, shell=True)
        
        # remove
        rm(f'{img}_b.nii.gz')
        
    files = [[f'{pth}_TPQA_TP_b01.nii.gz',\
              f'{pth}_TPQA_AP_b01_b_mask.nii.gz',\
              f'{pth}_TPQA_PA_b01_b_mask.nii.gz',\
              f'{pth}_TPQA_TP_b01_b_mask.nii.gz'], \
             [f'{pth}_TPQA_TP_b01.nii.gz',\
              f'{pth}_AP_b0s_mean_b_mask.nii.gz',\
              f'{pth}_PA_b0s_mean_b_mask.nii.gz',\
              f'{pth}_iout_mean_b_mask.nii.gz']]
        
    # Set alpha value for the images.
    a = 0.5
    # Set line width.
    l = 4
    
    names = [['1st b0', 'B01'], ['mean b0', 'B0M']]
    
    for x, fs in enumerate(files):

        fig = plt.figure(figsize=(12, 5))
        # plot with nilearn
        display = plotting.plot_anat(fs[0], cut_coords = (0, 0, 50), display_mode='ortho', cmap='gray', draw_cross = 0, figure = fig, title = f'{s} {names[x][0]}')
        display.add_contours(fs[1], alpha = a, antialiased=1, linewidths=l, colors=['red'], filled = 0)
        display.add_contours(fs[2], alpha = a, antialiased=1, linewidths=l, colors=['blue'], filled = 0)
        display.add_contours(fs[3], alpha = a, antialiased=1, linewidths=l, colors=['green'], filled = 0)
        display.annotate(scalebar=True)

    
        p_ap = Rectangle((0, 0), 1, 1, fc="red")
        p_pa = Rectangle((0, 0), 1, 1, fc="blue")
        p_tp = Rectangle((0, 0), 1, 1, fc="green")
        plt.legend([p_ap, p_pa, p_tp], ["AP", "PA", "TP"])

        display.savefig(f'{pth}_TP{names[x][1]}QA.png')
        display.close()

        plt.close(fig)
        
        # Make another plot but with more slices
        fig = plt.figure(figsize=(20, 12))
    
        display = plotting.plot_anat(fs[0], display_mode='mosaic', cmap='gray', draw_cross = 0, figure = fig, title = f'{s}')
        display.add_contours(fs[1], alpha = a, antialiased=1, linewidths=l, colors=['red'], filled = 0)
        display.add_contours(fs[2], alpha = a, antialiased=1, linewidths=l, colors=['blue'], filled = 0)
        display.add_contours(fs[3], alpha = a, antialiased=1, linewidths=l, colors=['green'], filled = 0)
        display.savefig(f'{pth}_TP{names[x][1]}MOSAICQA.png')
        display.close()

    rm(f'{pth}_TPQA_AP_b01.nii.gz')
    rm(f'{pth}_TPQA_PA_b01.nii.gz')
    rm(f'{pth}_TPQA_TP_b01.nii.gz')
    rm(f'{pth}_TPQA_AP_b01_b_mask.nii.gz')
    rm(f'{pth}_TPQA_PA_b01_b_mask.nii.gz')
    rm(f'{pth}_TPQA_TP_b01_b_mask.nii.gz')


def plt_topup(sid):
    """
    Generates multiple plots for QA purposes of the Topup process
    
    Created on Wed Apr 13 18:22:29 2022

    @author: aleksander
    """
    
    import matplotlib.pyplot as plt
    from os.path import join
    from nilearn import plotting
    
    pth = join('tmp', sid, sid)
    
    # plot mean AP, PA b0s and iout mean image
    iap = pth + '_AP_b0s_mean.nii.gz'
    fap = plt.figure(figsize=(12, 5))
    dap = plotting.plot_anat(iap, cut_coords = (0, 0, 50), display_mode='ortho', cmap='gray', draw_cross = 0, figure = fap, title = f'{sid} mean AP b0')
    dap.annotate(scalebar=True)
    dap.savefig(pth + '_APMB0QA.png')
    dap.close()
    plt.close(fap)

    ipa = pth + '_PA_b0s_mean.nii.gz'
    fpa = plt.figure(figsize=(12, 5))
    dpa = plotting.plot_anat(ipa, cut_coords = (0, 0, 50), display_mode='ortho', cmap='gray', draw_cross = 0, figure = fpa, title = f'{sid} mean PA b0')
    dpa.annotate(scalebar=True)
    dpa.savefig(pth + '_PAMB0QA.png')
    dpa.close()
    plt.close(fpa)
    
    ptp = pth + '_iout_mean.nii.gz'
    ftp = plt.figure(figsize=(12, 5))
    dpt = plotting.plot_anat(ptp, cut_coords = (0, 0, 50), display_mode='ortho', cmap='gray', draw_cross = 0, figure = ftp, title = f'{sid} mean IOUT b0')
    dpt.annotate(scalebar=True)
    dpt.savefig(pth + '_IOUTMQA.png')
    dpt.close()
    plt.close(ftp)
    
    # plot field coef
    fcoef = pth + '_AP-PA_topup_fieldcoef.nii.gz'
    fco = plt.figure(figsize=(12, 5))
    dfo = plotting.plot_epi(fcoef,  display_mode='mosaic', cmap='gray', draw_cross = 1, figure = fco, title = f'{sid} fieldcoef')
    dfo.savefig(pth + '_FCOEFQA.png')
    dfo.close()
    plt.close(fco)

    # fout
    fout = pth + '_fout.nii.gz'
    fou = plt.figure(figsize=(12, 5))
    dou = plotting.plot_epi(fout,  display_mode='mosaic', cmap='gray', draw_cross = 1, figure = fou, title = f'{sid} fout')
    dou.savefig(pth+'_FOUTQA.png')
    dou.close()
    plt.close(fou)

    # will notbe plotting the iout volumes as these are going to be corrected with EDDY anyhow. I am plotting mean image thoug
    '''    
    # plot iout
    iout = pth + '_iout.nii.gz'
    fio = plt.figure(figsize=(12, 5))
    dio = plotting.plot_epi(iout,  display_mode='mosaic', cmap='gray', draw_cross = 1, figure = fio, title = f'{sid} iout')
    dio.savefig(pth+'_IOUTQA.png')
    plotting.show()'''
    
    # Make outlines
    plt_topup_outlines(sid)

    
def mv_post_topup(sid):
    """
    Topup creates sequences of control images (jac, warpfield) and matrices (xfm)
    this fn moves those files into separate folders

    Parameters
    ----------
    sid : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    from os import mkdir
    from os import listdir
    from os.path import join 
    import shutil
    
    jacs = [f for f in listdir(join('tmp', sid)) if '_jac_' in f]
    warp = [f for f in listdir(join('tmp', sid)) if '_warpfield_' in f]
    xfms = [f for f in listdir(join('tmp', sid)) if '_xfm_' in f]

    mkdir(join('tmp', sid, 'topup_jacs'))
    mkdir(join('tmp', sid, 'topup_warpfields'))
    mkdir(join('tmp', sid, 'topup_xfms'))

    for f in jacs:
        shutil.move(join('tmp', sid, f), join('tmp', sid,'topup_jacs', f))
        
    for f in warp:
        shutil.move(join('tmp', sid, f), join('tmp', sid,'topup_warpfields', f))
        
    for f in xfms:
        shutil.move(join('tmp', sid, f), join('tmp', sid,'topup_xfms', f))
        
def run_apply_topup(sid):
    """
    DEPRECIATED

    Runs applytopup, not required as Eddy handels the distortion correction,

    Parameters
    ----------
    sid : STR
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    import subprocess as sb
    
    cmd = f'applytopup -i tmp/{sid}/{sid}_AP_denoised.nii.gz -x 1 \
        -a tmp/{sid}/acqparams.txt -t tmp/{sid}/{sid}_AP-PA_topup \
        -o tmp/{sid}/{sid}_AP_topup-applied -v -m jac'
        
    sb.run(cmd, shell=True)

def mk_b0s_topup_applied(sid):
    """
    DEPRECATED

    Extracts b0s from topup-applied DWI.

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.

    Returns
    -------
    - _AP_b0s_topup-applied.nii.gz
    - _AP_topup-applied_b0s.png (control plot)

    Created on Tue Apr 19 10:27:49 2022
    @author: aleksander nitka
    """

    from dipy.io.image import load_nifti, save_nifti
    from dipy.core.gradients import gradient_table
    import matplotlib.pyplot as plt
    import os
    from dipy.core.histeq import histeq
    import cmocean
    
    gtab = gradient_table(f'tmp/{sid}/{sid}_AP.bval', f'tmp/{sid}/{sid}_AP.bvec')
    
    dwi, affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_topup-applied.nii.gz'))
    
    b0s = dwi[:,:,:,gtab.b0s_mask]

    save_nifti(f'tmp/{sid}/{sid}_AP_b0s_topup-applied.nii.gz', b0s, affine)   
    
    # Control figure PA
    fig1, ax = plt.subplots(2, 5, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.15)
    fig1.suptitle(f'{sid} DWI (post topup) b0s', fontsize = 20)
    
    for i in range(0, b0s.shape[3]):
        
        ax.flat[i].imshow(histeq(b0s[:,:,42,i].T), cmap=cmocean.cm.tarn, interpolation='none',origin='lower')
        ax.flat[i].set_title(f'{i}')
        
    fig1.savefig(os.path.join('tmp', sid, f'{sid}_AP_topup-applied_b0s.png'))
 
