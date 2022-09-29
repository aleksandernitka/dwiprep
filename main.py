import argparse
from os import listdir as ls
from os import mkdir
from os.path import join, exists
import subprocess as sp
import numpy as np # not used to calulcate but to read text file

from fun.stauslog import StatusLog
from fun.qahtml import QaHtml

"""
TODO:
2. datain and dataout does not make sense in terms of multiple stages; rename to rawdata and derivatives folder
"""

class DwiPreprocessingClab():

    # Main analysis class for the dwi preprocessing pipeline.
    # Developed by Aleksander W. Nitka
    # Relies on the following software:
    # - FSL 6.0.5
    # - DIPY 1.5.0
    # - Fury 0.9.0
    # - Scikit-Learn
    # - Scikit-Image
    # - Nilearn

    def __init__(self, stage, mode, input, datain, dataout, threads, telegram=True, verbose=False, clean=True, copy=True):
        
        # Imports
        from os import isfile
        from os.path import join, exists
        from os import mkdir
        from os import listdir as ls
        import subprocess as sp
        from numpy import loadtxt
        from numpy import savetxt

        self.stage = stage
        self.mode = mode
        self.input = input
        self.datain = datain
        self.dataout = dataout
        self.threads = threads
        self.telegram = telegram
        self.verbose = verbose
        self.clean = clean
        self.copy = copy

        # Also mount some key dependencies for easy access
        self.ls = ls
        self.join = join
        self.exists = exists
        self.mkdir = mkdir
        self.isfile = isfile
        self.sp = sp
        self.loadtxt = loadtxt
        self.savetxt = savetxt

    ########################################
    # Checking methods #####################
    ########################################

    def check_inputs(self):
        
        # Check whether stage is correct
        if self.stage not in [1,2,3,4, 'gibbs', 'p2s', 'topup', 'eddy']:
            exit('Exit Error. Stage not recognised.')
        else:
            if self.verbose:
                print('Stage recognised.')
        
        # Check whether mode is correct
        if self.mode not in ['s', 'sub', 'l', 'list', 'a', 'all']:
            exit('Exit Error. Mode not recognised.')
        else:
            if self.verbose:
                print('Mode recognised.')

        # check if input is correct
        if self.input == None:
            exit('Exit Error. Input not provided.')
        else:
            # TODO
            if self.mode in ['s', 'sub']:
                pass
            elif self.mode in ['l', 'list']:
                pass
            elif self.mode in ['a', 'all']:
                pass
            else:
                print()
                exit('Input error. Input not recognised.')
            
    def check_telegram(self):
        # Check if telegram setup file is present and whether the user wants to use it
        
        if exists('send_telegram.py') and self.telegram == True:
            self.telegram = True
            if self.verbose:
                print('Telegram notifications are enabled')
            from send_telegram import sendtel
        else:
            self.telegram = False
            if self.verbose:
                print('Telegram not available')
    
    def check_container(self):
        # Check if we are using dipy and fsl from the containers
        # When creating the container an empty file is created in the /opt folder
        # so we can check if the container is loaded by checking if the file exists
        
        if not exists('/opt/dwiprep.txt'):
            exit('Exit error. Not running in required singularity image. Please ensure that the singularity image is loaded')
        else:
            if self.verbose:
                print('Singularity image loaded')

    def check_subid(self, sub):
        # Check if subject name contains sub- prefix
        if not sub.beginswith('sub-'):
            sub = 'sub-' + sub
        return sub

    def check_subject_indir(self, subid):
        # Check if subject directory exists
        if not self.exists(self.join(self.datain, subid)):
            print('Subject directory not found')
            return False
        else:
            if self.verbose:
                print('Subject directory found')
            return True

    def check_tmp_dir(self):
        # Simple method to check if tmp folder exists
        # create it if it does not exist
        from os.path import exists
        from os import mkdir
        if not exists('tmp'):
            mkdir('tmp')
            print('tmp folder created')
        else:
            if self.verbose:
                print('tmp directory already exists')

    def check_list_from_file(self):
        # Should only be run if mode is list or l
        # Return 1 is all is good, if fails return:
        # Check if input exists, fail = 2
        # Check if list is provided from a file, fail = 3
        # Check if the input is a list of subjects, fail = 4
        # If it is a list, check if the subjects are in the datain directory, fail = 5
        # If it is a list, check if the subjects are in the dataout directory
        
        if not self.exists(self.input):
            print(f'Input file not found: {self.input}')
            return 2

        if not self.isfile(self.input):
            print(f'Input is not a file: {self.input}')
            return 3

        if self.input.endswith('.txt') or self.input.endswith('.csv') or self.input.endswith('.tsv'):
            if self.verbose:
                print('Input is a text-readable file')
            
            with open(self.input, 'r') as f:
                subids = f.readlines()
                subids = [subid.strip() for subid in subids]
                print(f'List of subjects: {subids}')
                for subid in subids:
                    subid = self.check_subid(subid)
                    if not self.exists(self.join(self.datain, subid)):
                        print(f'Subject {subid} not found in datain directory')
                        return 5
                
            # Now all data has been checked in datain directory. 
        else:
            print('Input is not a text-readable file')
            return 4
        
        # If we get here, all is good
        return 1
    
    ########################################
    # Helping methods ######################
    ########################################

    def cp_rawdata(self, sub):
        # Copy raw data to tmp folder
        # Returns code:
        # 1 - success, 
        # 0 - failure, less than six files 
        # 2 - failure, more than six files, 
        # 3 - failure, no directory for subject    

        # Copy raw data to tmp folder
        # TODO change to self- bound methods
        import shutil
        from os.path import join
        from os import listdir as ls
        from os.path import exists
        
        # Check if tmp folder exists
        self.check_tmp_dir()
        
        # Check subject ID
        subid = self.check_subid(sub)

        # Check if subject directory exists
        if self.check_subject_indir(sub):
            # Dir exists, then list it's contents 
            bfs = [f for f in ls(join(self.datain, sub, 'dwi')) if '.DS_' not in f]
            # List only the files I am iterested in
            fsdwi = [f for f in bfs if '_SBRef_' not in f and '_ADC_' not in f and '_TRACEW_' not in f and '_ColFA_' not in f and '_FA_' not in f]
            
            # I expect six files exactly
            if len(fsdwi) != 6:
                print(f'{sub} has {len} dwi files in the rawdata folder {self.datain}. Please check.')
                if len(fsdwi) < 6:
                    return 0
                else:
                    return 2
            
            else:
                # if we have 6 dwi files then copy them to tmp folder
                # Create tmp folder for subject
                if exists(join(self.datain, sub)) is False:
                    mkdir(join(self.datain, sub))
                    if self.verbose:
                        print(f'{sub} tmp folder created')

                # Copy files to tmp folder, for all files in fsdwi
                for f in fsdwi:
                    # Set name depending on the direction
                    if '_AP_' in f:
                        fn = f'{sub}_AP.{f.split(".")[-1]}'
                    elif '_PA_' in f:
                        fn = f'{sub}_PA.{f.split(".")[-1]}'
                    # Copy file
                    if self.verbose:
                        print(f'cp {join(self.datain, sub, "dwi", f)} ---> {join(args.tmp, sub, fn)}')
                    
                    shutil.copy(join(self.datain, sub, 'dwi', f), join('tmp', sub, fn))

                # All done return 1
                return 1
        else:
            print(f'{subid} not found in {self.datain}')
            return 3

    ########################################
    # DWI Preprocessing ####################
    ########################################

    def gibbs(self, sub):
        # Run Gibbs ringing correction, for each subject

        # Subid should have been checked
        # Subject dir should have been checked
        # tmp folder should have been checked
        # raw data should have been checked

        # copy raw data to tmp folder
        o = self.cp_rawdata(sub) # will return status code

        # if copied ok, then run gibbs
        if o == 1:
            if self.verbose:
                print(f'Running gibbs ringing correction for {sub}')
            
            self.sp.run(f'dipy_gibbs_ringing {self.join("tmp", sub, sub + "_AP.nii")} {self.join("tmp", sub, sub + "_AP_gib.nii")}', shell=True)
            self.sp.run(f'dipy_gibbs_ringing {self.join("tmp", sub, sub + "_PA.nii")} {self.join("tmp", sub, sub + "_PA_gib.nii")}', shell=True)

            # Create plots for QA
            # Create dirs to plot to
            self.mkdir(self.join('tmp', sub, 'imgs'))
            self.mkdir(self.join('tmp', sub, 'imgs', 'gibbs'))

            # Plot AP RAW
            self.sp.run(f'fun/gifdwi.py {self.join("tmp", sub, sub + "_AP.nii")} {self.join("tmp", sub, "imgs", "gibbs", sub + "_AP_raw.gif")} -t AP_RAW', shell=True)
            # plot AP Gibbs
            self.sp.run(f'fun/gifdwi.py {self.join("tmp", sub, sub + "_AP_gib.nii")} {self.join("tmp", sub, "imgs", "gibbs", sub + "_AP_gib.gif")} -t AP_GIBBS', shell=True)

            # Plot AP Comparison
            plot_i1 = self.join("tmp", sub, sub + "_AP.nii")
            plot_i2 = self.join("tmp", sub, sub + "_AP_gib.nii")
            self.sp.run(f'fun/compare.py {sub} {plot_i1} {plot_i2} \
                {self.join("tmp", sub, "imgs", "gibbs", sub + "_ap_rawgib")}\
                 -v 0 1 2 3 4 5 6 7 8 ', shell=True)

            # Plot PA Comparison
            plot_i1 = self.join("tmp", sub, sub + "_PA.nii")
            plot_i2 = self.join("tmp", sub, sub + "_PA_gib.nii")
            self.sp.run(f'fun/compare.py {sub} {plot_i1} {plot_i2} \
                {self.join("tmp", sub, "imgs", "gibbs", sub + "_pa_rawgib")}\
                 -v 0 1 2 3 4 ', shell=True)
        else:
            # Copy was not successful, return error code
            return o

        

        # copy output to dataout folder


        

    def p2s(self):
        # TODO
        # Run patch2self
        pass

    def eddy(self):
        # TODO
        pass

    def topup(self):
        # TODO
        pass

args = argparse.ArgumentParser(description="DWI preprocessing pipeline script")
args.add_argument('stage', help="Stage of the pipeline to run", choices=[1,2,3,4,5, 'gibbs', 'p2s', 'topup', 'eddy', 'qa'])
args.add_argument('mode', help='Mode to run in, s or sub for a single subject id,\
    l or list for a list of subject ids, a or all for all subject ids that are going to be found in the data directory', choices=['s', 'sub', 'l', 'list', 'a', 'all'])
args.add_argument('datain', help='Path to data directory; either the rawdata or derivatives folder with all subs- inside')
args.add_argument('dataout', help='Path to output directory; most likely the derivatives folder')
args.add_argument('-i', '--input', help='Input: subject id if mode == s, path to list of subject ids if mode == l, do not use if mode == a', required=False)
args.add_argument('-t', '--threads', help='Number of threads to use', type=int, default=-1)
args.add_argument('-noclean', '--noclean', help='Do not clean tmp dir but move to dataout', action='store_true', default=False)
args.add_argument('-nocopy', '--nocopy', help='Do not copy data to dataout', action='store_true', default=False)
args.add_argument('-notg', '--notelegram', help='Do not send telegram message', action='store_true', default=False)
a = args.parse_args()

"""
Perform sanity checks on input and locate required files
"""
# Check if we are using dipy and fsl from the containers
# When creating the container an empty file is created in the /opt folder
# so we can check if the container is loaded by checking if the file exists
"""
if not exists('/opt/dwiprep.txt'):
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
Initialise QA stuff
"""
dwiqa = QaHtml('QAtest', subs, 'DWIPREP')

"""
Run processing pipeline, this is run for each subject at each step,
that is, all subject are de-ringed, then all subjects are denoised, etc.
this is because the output of one step is the input of the next step and
some of the steps are computationally expensive and paralellised and some 
(topup) are not.
"""

if a.stage in [1, 'gibbs']:
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
    
