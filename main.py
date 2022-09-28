import argparse
from distutils.sysconfig import get_config_h_filename
from os import listdir as ls
from os import mkdir
from os.path import join, exists
import subprocess as sp
import numpy as np # not used to calulcate but to read text file
from fun.stauslog import StatusLog

"""
This file should be run only after the singularity image has been loaded (singularity/dwi_preproc.sif). 
In such way it is ensured that the required software (dipy, fsl) are available. Use the following 
command to initiate singularity image:

singularity shell --bind /mnt:/mnt singularity/dwi_preproc.sif

It will bind the /mnt folder to the singularity image. This is required for the script to be able to
access the data.

TODO:
1. Run a single step instead of sequence of steps, if 1+ run all from 1st but if 1 run just this one
2. datain and dataout does not make sense in terms of multiple stages; rename to rawdata and derivatives folder
"""

args = argparse.ArgumentParser(description="DWI preprocessing pipeline script")
args.add_argument('mode', choices=['s', 'sub', 'l', 'list', 'a', 'all'], help='Mode to run in, s or sub for a single subject id,\
    l or list for a list of subject ids, a or all for all subject ids that are going to be found in the data directory')
args.add_argument('datain', help='Path to data directory')
args.add_argument('dataout', help='Path to output directory')
args.add_argument('-i', '--input', help='Input: subject id if mode == s, path to list of subject ids if mode == l, do not use if mode == a', required=False)
args.add_argument('-r', '--run', help='Where to start or pickup process from: 1. Gibbs de-ringing, 2. Patch2Self denoising, 3. TopUp estimaton,\
    4. Eddy, 5.Quality Reports.', default=1, metavar='[1-5]', type=int, choices=[1, 2, 3, 4, 5])
args.add_argument('-t', '--threads', help='Number of threads to use', type=int, default=-1)
args.add_argument('-noclean', '--noclean', help='Do not clean tmp dir but move to dataout', action='store_true', default=False)
args.add_argument('-nocopy', '--nocopy', help='Do not copy data to dataout', action='store_true', default=False)
args.add_argument('-notg' '--notelegram', help='Do not send telegram message', action='store_true', default=False)
a = args.parse_args()

"""
Perform sanity checks on input and locate required files
"""
# Check if we are using dipy and fsl from the containers
"""
if not exists('/opt/miniconda-dwi/bin/dipy_info'):
    print('Could not locate dipy_info, please ensure that the singularity image is loaded')
    exit(1)"""
# TODO
# alternative method would be to touch a dummy file inside the container and then check for existence

# Check if telegram config files are present:
if exists('send_telegram.py') and not a.notelegram:
    telegram = True
    from send_telegram import sendtel
else:
    telegram = False

# Check if input is valid
if a.mode in ['s', 'sub']:
    # if mode is set as single subject, check if input is provided
    if not a.input:
        print('Please provide a subject id with the -i or --input flag')
        exit(1)
    else:
        # check is prefix is sub-
        if not a.input.startswith('sub-'):
            a.input = 'sub-' + a.input
        # check if subject id exists in data directory
        if not exists(join(a.datain, a.input)):
            print(f'Could not locate {a.input} in {a.datain}, exiting...')
            exit(1)
        else:
            # This ensures that the subject id is a list
            # and so we can use the same code for all modes
            subs = [a.input]
elif a.mode in ['l', 'list']:
    if not a.input:
        print('Please provide a path to a list of subject ids with the -i or --input flag')
        exit(1)
    elif not exists(a.input):
        print(f'Could not locate {a.input}, exiting...')
        exit(1)
    else:
        # Load subject ids from list
        subs = np.loadtxt(a.input, dtype=str)
        for s in subs:
            # add prefix sub- if not there
            if not s.startswith('sub-'):
                s = 'sub-' + s
            if not exists(join(a.datain, s)):
                print(f'Could not locate {s} in {a.datain}, exiting...')
                exit(1)
            else:
                print(f'Found {s} in {a.datain}')
elif a.mode in ['a', 'all']:
    if not exists(a.datain):
        print(f'Could not locate {a.datain}, exiting...')
        exit(1)
    else:
        subs = [f for f in ls(a.datain) if f.startswith('sub-')]
        print(f'Found {len(subs)} subjects in {a.datain}')

# Check if output directory exists
if not exists(a.dataout) and not a.nocopy:
    print(f'Could not locate {a.dataout}, please create it or ensure access. Exiting...')
    exit(1)

# Check if tmp dir exists
if not exists('tmp'):
    print('Creating tmp directory...')
    mkdir('tmp')

"""
Initialise logging
"""
log = StatusLog('status.log')

"""
Establish processing pipeline based on input
"""
process = np.array([1,1,1,1,1])
if a.run != 1:
    # Set all previous steps to 0
    # so they are not run
    process[0:a.run-1] = 0

log.info('ALL',f'Processing pipeline: {process}')
"""
Run processing pipeline, this is run for each subject at each step,
that is, all subject are de-ringed, then all subjects are denoised, etc.
this is because the output of one step is the input of the next step and
some of the steps are computationally expensive and paralellised and some 
(topup) are not.
"""

if process[0]:
    log.info('ALL', 'Running Gibbs de-ringing')
    for i, s in enumerate(subs):
        
        # log
        log.subjectStart(s, 'Gibbs de-ringing')
        
        """
        1. Run Gibbs de-ringing and create control plot for some example volumes
        """

        print(f'Copying data for {s} ({i+1}/{len(subs)})')
        
        # Copy data to tmp directory
        try:
            sp.run(f'python fun/copy_dwi.py {s} {a.datain} tmp -v', shell=True)
            log.ok(s, 'Gibbs de-ringing, Copying data')
        except:
            log.error(s, 'Gibbs de-ringing, Copying data')
            continue

        # Created dirs for QA plots
        sp.run(f'mkdir tmp/{s}/imgs', shell=True)
        sp.run(f'mkdir tmp/{s}/imgs/gibbs', shell=True)
        
        # Create control plot for raw images (gif)
        try:
            nii_file = join('tmp', s, f'{s}_AP.nii')
            gif_file = join('tmp', s, 'imgs', 'gibbs', f'{s}_raw.gif')

            sp.run(f'python fun/gifdwi.py {nii_file} {gif_file} -t "{s} AP RAW"', shell=True)
            log.ok(s, 'Gibbs de-ringing, Creating control plot RAW')
        except:
            log.error(s, 'Gibbs de-ringing, Creating control plot RAW')
            continue
        
        # Run Gibbs de-ringing
        print(f'Running Gibbs de-ringing for {s} ({i+1}/{len(subs)})')
        try:
            sp.run(f'dipy_gibbs_ringing tmp/{s}/{s}_AP.nii --num_processes {a.threads} --out_unring tmp/{s}/{s}_AP_gib.nii.gz', shell=True) 
            sp.run(f'dipy_gibbs_ringing tmp/{s}/{s}_PA.nii --num_processes {a.threads} --out_unring tmp/{s}/{s}_PA_gib.nii.gz', shell=True)
            log.ok(s, 'Gibbs de-ringing, Running Gibbs de-ringing')
        except:
            log.error(s, 'Gibbs de-ringing, Running Gibbs de-ringing')
            continue

        # Create control plot GIF plus selected volumes compared to raw
        print(f'Creating QA plots for {s} ({i+1}/{len(subs)})')
        try:
            nii_file = join('tmp', s, f'{s}_AP_gib.nii.gz')
            gif_file = join('tmp', s, 'imgs', 'gibbs', f'{s}_gibbs.gif')

            sp.run(f'python fun/gifdwi.py {nii_file} {gif_file} -t "{s} AP gib"', shell=True)
            log.ok(s, 'Gibbs de-ringing, Creating control plot GIBBS corrected')
        except:
            log.error(s, 'Gibbs de-ringing, Creating control plot GIBBS corrected')
            continue

        try:
            sp.run(f'python fun/compare.py {s} tmp/{s}/{s}_AP.nii tmp/{s}/{s}_AP_gib.nii.gz \
            tmp/{s}/imgs/gibbs/{s}_ap_rawgib -v 0 1 2 3 4 5 6 7 8 9 10', shell=True)
            
            sp.run(f'python fun/compare.py {s} tmp/{s}/{s}_PA.nii tmp/{s}/{s}_PA_gib.nii.gz \
            tmp/{s}/imgs/gibbs/{s}_pa_rawgib -v 0 1 2 3 ', shell=True)
            
            log.ok(s, 'Gibbs de-ringing, Creating compare plot GIBBS corrected and RAW')
        except:
            log.error(s, 'Gibbs de-ringing, Creating compare plot GIBBS corrected and RAW')
            continue
        
        if not a.nocopy:
            # Copy all data back to dataout (most likely derivatives) directory
            print(f'Copying data to {a.dataout} for {s} ({i+1}/{len(subs)})')
            try:
                sp.run(f'cp -fR tmp/{s} {a.dataout}', shell=True)
                log.ok(s, f'Gibbs de-ringing, Copying data to {a.dataout}')
            except:
                log.error(s, f'Gibbs de-ringing, Copying data to {a.dataout}')
                continue
        else:
            log.info(s, f'Gibbs de-ringing --nocopy flag, Skipping copying data to {a.dataout}')

        if not a.noclean:
            # Remove tmp directory
            print(f'Removing tmp directory for {s} ({i+1}/{len(subs)})')
            try:
                sp.run(f'rm -fR tmp/{s}', shell=True)
                log.ok(s, 'Gibbs de-ringing, Removing tmp directory')
            except:
                log.error(s, 'Gibbs de-ringing, Removing tmp directory')
                continue
        else:
            log.info(s, 'Gibbs de-ringing --noclean flag, Skipping tmp directory removal')
         
        log.subjectEnd(s, 'Gibbs de-ringing')

    # notify user that this step is complete
    log.ok('ALL', 'Gibbs de-ringing complete')
    if telegram:
        sendtel('Gibbs de-ringing complete')

if process[1]:
    """
    2. Run Patch2Self denoising and create control plot for some example volumes
    """ 
    pass

if process[2]:
    """
    3. Run TopUp estimation
    """
    pass

if process[3]:
    """
    4. Run Eddy
    """
    pass
if process[4]:
    """
    5. Run Quality Reports
    """
    pass