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
    totaln = totaln - totaln # Should 0
    
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
          
def run_topup(sid, pre_cmd):
    """
    Using subprocess this fn runs the fsl topup. Noting more nothing less. 

    Parameters
    ----------
    sid : STR
        Subject id with 'sub' prefix.
    pre_cmd : STR
        Command that should be fed to bash before running the subprocess,
        this can be source or freesurfer activation, divide comands with ';'

    Returns
    -------
    - Standard topup outputs, including fout and iout

    """
    import subprocess as sb
    
    """
    tp_cmd = f'topup --imain=tmp/{sid}_AP-PA_b0s --datain=tmp/acqparams.txt \
        --out=tmp/{sid}_AP-PA_topup -v --fout=tmp/{sid}_AP-PA_fout \
        --iout=tmp/{sid}_AP-PA_iout -m jac --config=b02b0.cnf'
        
    tp_cmd = f'topup --imain=tmp/{sid}_AP-PA_b0s --datain=tmp/acqparams.txt \
        --out=tmp/{sid}_AP-PA_topup -v --fout=tmp/{sid}_AP-PA_fout \
        --iout=tmp/{sid}_AP-PA_iout -m jac --jacout={sid}_jac --dfout={sid}_warpfield \
        --config=b02b0.cnf'
    """
    tp_cmd = f'topup --config=b02b0.cfn --datain=tmp/{sid}/acqparams.txt \
        --imain=tmp/{sid}/{sid}_AP-PA_b0s --out=tmp/{sid}/{sid}_AP-PA_topup \
        --iout=tmp/{sid}/{sid}_iout --fout=tmp/{sid}/{sid}_fout \
        --m jac --jacout=tmp/{sid}/{sid}_jac --logout=tmp/{sid}/{sid}_topup.log \
        --rbmout=tmp/{sid}/{sid}_xfm --dfout=tmp/{sid}/{sid}_warpfield'
    
    
    sb.run(pre_cmd + ' ' + tp_cmd, shell=True)

def mk_bet_brain_mask(sid, pre_cmd):
    """
    Runs BET brain extraction and mask algo, then plots for QA

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.
    pre_cmd : str
        Command to execute in bash to setup the environment variables and PATH.

    Returns
    -------
    - Binary mask
    - Extracted brain image
    - 3 x plot for QA

    """
    import os
    import matplotlib.pyplot as plt
    from dipy.io.image import load_nifti
    from dipy.core.histeq import histeq
    import cmocean
    import subprocess as sb
    
    # run bet in bash
    cmd_bet = f'bet tmp/{sid}/{sid}_AP_b0s_topup-applied_mean tmp/{sid}/{sid}_AP_b0s_topup-applied_bet -m'
    sb.run(pre_cmd + ' ' + cmd_bet, shell=True)
    
    mask, __ = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_bet_mask.nii.gz'))
    dwi, __ = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_mean.nii.gz'))
    
    
    fig1, ax = plt.subplots(1, 3, figsize=(8, 3), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(histeq(dwi[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[1].imshow(histeq(dwi[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[2].imshow(histeq(dwi[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', sid, f'{sid}_brainmask_bet.png'))

def mk_otsu_brain_mask(sid):
    """
    BET generated brain mask is not too good and often comes significantly eroded
    with regards to the dwi brain. The OTSU method from DIPY seems to do a 
    better job, but it is recomended to check anyhow. 

    Parameters
    ----------
    sid : str
        Subject id with 'sub' prefix.

    Returns
    -------
    - Bianry brain mask
    - Extracted brain image
    - 3 x control QA plot
    """
    
    import os
    from dipy.segment.mask import median_otsu
    from dipy.io.image import load_nifti, save_nifti
    import matplotlib.pyplot as plt
    from dipy.core.histeq import histeq
    import cmocean
    import numpy as np
    
    b0, b0_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_mean.nii.gz'))
    
    # Make mask with median_otsu method, default params
    b0_mask, mask = median_otsu(b0)
    
    # save to nifti
    save_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_otsu.nii.gz'), b0_mask, b0_affine)
    save_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_otsu_mask.nii.gz'), mask.astype(np.float32), b0_affine)
    
    # control plot
    fig1, ax = plt.subplots(1, 3, figsize=(8, 3), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
    
    ax.flat[0].imshow(histeq(b0[:,:,42].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[0].imshow(mask[:,:,42].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[1].imshow(histeq(b0[:,50,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[1].imshow(mask[:,50,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    ax.flat[2].imshow(histeq(b0[50,:,:].T), interpolation = 'none', origin = 'lower', cmap = cmocean.cm.tarn)
    ax.flat[2].imshow(mask[50,:,:].T, alpha=.5, interpolation = 'none', origin = 'lower')
    
    fig1.savefig(os.path.join('tmp', sid, f'{sid}_brainmask_otsu.png'))

def mk_index_eddy(sid):
    
    """
    Eddy requires index file with has the same amount of rows as the dwi has volumes
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
    
def mk_brain_edges(sid):
    """
    Simple toy function which plots series of edges with various sigma. May be 
    useful for some superimposed plotting of two images

    Parameters
    ----------
    sid : str 
        Subject is with sub prefix.

    Returns
    -------
    None.

    """
    
    # TODO Try with PIL filters
    """
    from PIL import Image
    with Image.open(filename) as img:
        img.load()
    >>> img_gray = img.convert("L")
    >>> edges = img_gray.filter(ImageFilter.FIND_EDGES)
    >>> edges.show()
    """
    
    import matplotlib.pyplot as plt
    from skimage.feature import canny
    from dipy.io.image import load_nifti
    import os
    from dipy.core.histeq import histeq
    import cmocean

    i, affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP_b0s_topup-applied_otsu.nii.gz'))

    plt.imshow(histeq(i[:,:,42].T), cmap = cmocean.cm.tarn, interpolation = 'none', origin = 'lower', )

    fig1, ax = plt.subplots(2, 3, figsize=(16, 12), subplot_kw={'xticks': [], 'yticks': []})
    fig1.subplots_adjust(hspace=0.05, wspace=0.05)

    sigmas = [1, 2, 3, 4, 5, 6]

    for n, s in enumerate(sigmas):
        
        edg = canny(histeq(i[:,:,42]), sigma = s)
        ax.flat[n].imshow(edg.T, interpolation = 'none', origin = 'lower', cmap='gray')
             
def mk_b0s_topup_applied(sid):

    """
    Extracts all b0s from the topup corrected volume (dwi)
    
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
    # TODO add histeq and cmap
    
    # Load dwi
    dwi_ap, dwi_ap_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_AP.nii'))
    dwi_pa, dwi_pa_affine = load_nifti(os.path.join('tmp', sid, f'{sid}_PA.nii'))
    
    # load bval
    bvals_ap = np.loadtxt(os.path.join('tmp', sid, f'{sid}_AP.bval'))
    bvals_pa = np.array([5.,5.,5.,5.,5.])
    
    # Process AP
    dwi_ap_den = patch2self(dwi_ap, bvals_ap, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)
    # Save NII
    save_nifti(os.path.join('tmp', sid, f'{sid}_AP_denoised.nii.gz'), dwi_ap_den, dwi_ap_affine)
    
    # Process PA
    dwi_pa_den = patch2self(dwi_pa, bvals_pa, model='ols', shift_intensity=True, clip_negative_vals=False, b0_threshold=50, verbose=True)
    save_nifti(os.path.join('tmp', sid, f'{sid}_PA_denoised.nii.gz'), dwi_pa_den, dwi_pa_affine)
    
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
    
    # plots for AP
    for i, vs in enumerate(range(0, dwi_ap_den.shape[3])):
    
    
        # computes the residuals
        rms_diff = np.sqrt((dwi_ap[:,:,s,vs] - dwi_ap_den[:,:,s,vs]) ** 2)
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    
        fig1.subplots_adjust(hspace=0.05, wspace=0.05)
        fig1.suptitle(f'{sid} AP vol={vs} bval={int(bvals_ap[i])}', fontsize =20)
    
        ax.flat[0].imshow(dwi_ap[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[0].set_title(f'Original, vol {vs}')
        ax.flat[1].imshow(dwi_ap_den[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[1].set_title('Denoised Output')
        ax.flat[2].imshow(rms_diff.T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[2].set_title('Residuals')
        
        sfig = os.path.join(png_dir, f'{sid}_ap_bv-{int(bvals_ap[i])}_v-{vs}.png')
        hfig = os.path.join(sid, f'{sid}_p2s_pngs', f'{sid}_ap_bv-{int(bvals_ap[i])}_v-{vs}.png')
        fig1.savefig(sfig)
        
        # Add to html
        html += f'<img src="{hfig}"><br>'
        plt.close()
    
    html+="<br><br><h2 id = 'pa'>PA Volumes</h2><br><br><p>Please note that PA volumes were denoised assuming five b-vals of 5.<br><br>"
    
    # Plots for PA
    for i, vs in enumerate(range(0, dwi_pa_den.shape[3])):
    
        # computes the residuals
        rms_diff = np.sqrt((dwi_pa[:,:,s,vs] - dwi_pa_den[:,:,s,vs]) ** 2)
    
        fig1, ax = plt.subplots(1, 3, figsize=(12, 6),subplot_kw={'xticks': [], 'yticks': []})
    
        fig1.subplots_adjust(hspace=0.05, wspace=0.05)
        fig1.suptitle(f'{sid} PA vol={vs} bval={int(bvals_pa[i])}', fontsize=20)
    
        ax.flat[0].imshow(dwi_pa[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[0].set_title(f'Original, vol {vs}')
        ax.flat[1].imshow(dwi_pa_den[:,:,s,vs].T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[1].set_title('Denoised Output')
        ax.flat[2].imshow(rms_diff.T, cmap='gray', interpolation='none',origin='lower')
        ax.flat[2].set_title('Residuals')
    
        sfig = os.path.join(png_dir, f'{sid}_pa_bv-{int(bvals_pa[i])}_v-{vs}.png')
        hfig = os.path.join(sid, f'{sid}_p2s_pngs', f'{sid}_pa_bv-{int(bvals_pa[i])}_v-{vs}.png')
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
     
def cp_dwi_files(sid, hmri, rawdata, where):
    
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

    # cp t1 to tmp
    try:
        shutil.copy(os.path.join(hmri, sid, 'Results', f'{sid}_synthetic_T1w.nii'), os.path.join(where, f'{sid}_T1w.nii'))
    except:
        print(f'{sid} error copying t1w')
        return None