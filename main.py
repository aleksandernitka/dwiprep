
class DwiPreprocessingClab():

    # TODO - at each step of the pipeline drop a file with some details, time and date as infor for qa.
    # TODO - delcare class with raw dir and derrivatives dir, this may allow better interoprability of order.
    # Main analysis class for the MRI processing pipeline
    # Standarises some of the processing steps
    # Developed by Aleksander W. Nitka
    # Relies on the following software:
    # - FSL 6.0.5
    # - DIPY 1.5.0
    # - Fury 0.9.0
    # - MRtrix3 3.0.2
    # - Scikit-Learn 
    # - Scikit-Image 
    # - Nilearn 

    def __init__(self, task, mode, gibbs_method='mrtrix3', input=None, datain=None, dataout=None, \
        threads=-1, telegram=True, verbose=False, clean=True, \
        copy=True, log=True, check_container=True, n_coils=32):
        
        # Imports
        from os.path import join, exists, dirname, split, basename, isfile, isdir
        from os import mkdir, makedirs, remove
        from os import listdir as ls
        from dipy.io.image import load_nifti, save_nifti
        import subprocess as sp
        from datetime import datetime as dt
        from shutil import copyfile, copytree, rmtree


        self.task = task # name of the task performed, used for logging. Can be anything but keep it brief
        self.mode = mode # mode of the pipeline to be run, either single subject, list of subjects or all subjects in a directory
        self.input = input # input file or subject id to be processed
        self.datain = datain # input directory
        self.dataout = dataout # output directory
        self.threads = threads # number of threads to be used, when possible to set
        self.telegram = telegram # whether to send telegram notifications
        self.verbose = verbose # whether to print verbose messages
        self.clean = clean # whether to clean up the tmp folder after processing
        self.copy = copy # whether to copy the data from tmp to the dataout folder
        self.log = log # whether to log the processing
        self.n_coils = n_coils # number of coils used for the acquisition
        self.gibbs_method = gibbs_method # method to be used for gibbs ringing correction, either mrtrix or dipy

        # Also mount some key dependencies for easy access
        self.ls = ls
        self.join = join
        self.split = split
        self.exists = exists
        self.mkdir = mkdir
        self.isfile = isfile
        self.isdir = isdir
        self.remove = remove
        self.makedirs = makedirs
        self.dirname = dirname
        self.basename = basename
        self.copyfile = copyfile
        self.copytree = copytree
        self.rmtree = rmtree
        self.sp = sp
        self.load_nifti = load_nifti
        self.save_nifti = save_nifti
        self.dt = dt

        # Start logging
        self.log_start(self.task)

        # Performs all neccessary checks before starting the processing
        # This should be step 1 in the main script, ALWAYS

        # Check if we are using the correct singularity image
        if check_container:
            s, m = self.check_container()
            if not s:
                self.log_error('INIT', m)
                exit(m)
            else:
                pass
        else:
            self.log_info('INIT', 'Container check skipped.')
            pass
        
        # Check if the input is correct
        s, m = self.check_inputs()
        if not s:
            self.log_error('INIT', m)
            exit(m)
        else:
            pass
        
        # Check the tmp dir
        s, m = self.check_tmp_dir()
        if not s:
            self.log_error('INIT', m)
            exit(m)
        else:
            pass

        # Check telegram - no return value
        self.check_telegram()

        # Check if gibbs method is good.
        if self.gibbs_method not in ['dipy', 'mrtrix3']:
            print('Invalid method, allowed methods are dipy and mrtrix3')
            self.log_error(f'{sub}', f'gibbs: Invalid method: {self.gibbs_method}')
            return [False, 'Invalid method']
        
        self.log_ok('INIT', 'All checks passed')
        print('All initial checks passed. Starting processing')
        
    ########################################
    # Logging and notifications ############
    ########################################

    def log_start(self, task):
        if self.log:
            # logging setup
            # Check if the log directory exists
            if not self.exists('logs'):
                self.mkdir('logs')
            # Create a timestamp
            self.logtimestamp = self.dt.now().strftime('%Y%m%d%H%M%S')
            # create a log file
            self.logfilename = self.join('logs', f'{self.logtimestamp}_{task.replace(" ","").lower()[:10]}.log')
            self.file = open(self.logfilename, 'w')
            self.file.write(f'{self.dt.now()}\tALL\tNA\tStatusLog initialised.')
            self.file.close()
        
    def log_ok(self, id, message):
        if self.log:
            # Logs successful completion of a task
            self.file = open(self.logfilename, 'a')
            self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')
            self.file.close()
    
    def log_error(self, id, message):
        if self.log:
            # Logs errors or exceptions
            self.file = open(self.logfilename, 'a')
            self.file.write(f'\n{self.dt.now()}\t{id}\tERROR\t{message}')
            self.file.close()

    def log_warning(self, id, message):
        if self.log:
            # Logs warnings
            self.file = open(self.logfilename, 'a')
            self.file.write(f'\n{self.dt.now()}\t{id}\tWARNING\t{message}')
            self.file.close()

    def log_info(self, id, message):
        if self.log:
            # Logs information
            self.file = open(self.logfilename, 'a')
            self.file.write(f'\n{self.dt.now()}\t{id}\tINFO\t{message}')
            self.file.close()
    
    def log_deltaTstart(self):
        if self.log:
            # Logs the start of a deltaT processing
            self.file = open(self.logfilename, 'a')
            self.start = self.dt.now()
            self.file.close()

    def log_deltaTend(self, id, task):
        if self.log:     
            # Logs the end of a deltaT processing
            self.file = open(self.logfilename, 'a')
            self.end = self.dt.now()
            self.file.write(f'\n{self.end}\t{id}\tTASKEND\t{task}: {self.end - self.start}')
            self.file.close()

    def log_subjectStart(self, id, task):
        if self.log:
            # Logs the start of a subject processing
            self.file = open(self.logfilename, 'a')
            self.subStart = self.dt.now()
            self.file.write(f'\n{self.subStart}\t{id}\tSUBSTART\t{task}: Subject started')
            self.file.close()
        
    def log_subjectEnd(self, id, task):
        if self.log:
            # Logs the end of a subject processing
            self.file = open(self.logfilename, 'a')
            self.subEnd = self.dt.now()
            self.file.write(f'\n{self.dt.now()}\t{id}\tSUBEND\t{task}: Subject ended, duration: {self.subEnd - self.subStart}')
            self.file.close()
        
    def log_close(self):
        if self.log:
            self.file = open(self.logfilename, 'a')
            self.file.write(f'\n{self.dt.now()}\tALL\tNA\tStatusLog closed.')
            # Closes the log file
            self.file.close()

    def log_subdump(self, subjects):
        if self.log:
            # Dumps the list of subjects to the file
            self.subdumpfile = open(self.join('logs', f'{self.logtimestamp}_{self.task.replace(" ","").lower()[:10]}_subjects.log'), 'w')
            self.subdumpfile.write(str(subjects))
            self.subdumpfile.close()

    ########################################
    # Checking methods #####################
    ########################################

    # Below methods were prepared to ease the process of checking the data
    # before it gets processed further, to ensure that the data is in the
    # directory and all files are present.
    # Appropriate checks can minimise the risk of errors and crashes
    #
    # All check_ methods that are critical and cannot correct it should return a list with two items:
    #   - first item is a boolean value, True if the check passed, False if it failed
    #   - second item is a string with the error message if the check failed

    def check_inputs(self):
        # This part of the code checks if the input data is present and valid
        # For all three modes of operation, it checks if the input data is present
        # then ends up with a list of subjects to be processed loaded as self.subs
        # Furthermore, it returns True if all checks passed, False if any of them failed
        # together with a message what went wrong

        # load all subjects into the below list
        self.subs = None

        # Check whether mode is correct
        if self.mode not in ['s', 'sub', 'l', 'list', 'a', 'all']:
            self.log_error('INIT', 'Exit Error. Mode not recognised.')
            return [False, 'Exit Error. Mode not recognised.']
        else:
            if self.verbose:
                self.log_ok('INIT', 'Mode recognised')
                print('Mode recognised.')

        # check if input is correct, based on mode selected
        if self.input == None and self.mode not in ['a', 'all']:
            self.log_error('INIT', 'Exit Error. Input not specified.')
            return [False, 'Exit Error. Input not provided.']
        else:
            # For subject we do not need to check if the file exists
            # That is done in the loop
            if self.mode in ['s', 'sub']:
                if self.verbose:
                    print('Input recognised. Single subject mode.')
                # Check if subject name contains sub- prefix
                # make a list of inputs from one input, so all modes
                # can be treated the same way
                self.subs = [self.check_subid(self.input)]
                self.log_ok('INIT', 'Input recognised; single subject mode.')
                return [True, 'Input recognised. Single subject mode.']
            
            # For the list mode we need to check if the file exists
            elif self.mode in ['l', 'list']:
                if self.verbose:
                    print('Input recognised. List of subjects mode.')
                self.log_ok('INIT', 'Input recognised; list of subjects mode.')
                if self.isfile(self.input):
                    # DO not need to check if the file is empty, do it at the loop level
                    # But read the file in and make a list of inputs
                    # Read the file and make a list of inputs
                    try:
                        with open(self.input, 'r') as f:
                            self.subs = f.readlines()
                            self.subs = [self.check_subid(x.strip()) for x in self.subs]
                        self.log_ok('INIT', 'Input recognise and read; list of subjects mode.')
                        return [True, 'Input recognised and loaded. List of subjects mode.']
                    except:
                        self.log_error('INIT', 'Exit Error. Input file could not be read.')
                        return [False, 'Exit Error. Input file not readable.']
                else:
                    self.log_error('INIT', f'Exit Error. Input file {self.input} not found.')
                    return [False, 'Exit Error. Input file not found.']
            
            # all mode needs a valid directory
            elif self.mode in ['a', 'all']:
                if self.verbose:
                    print('Input recognised. All subjects mode.')
                self.log_ok('INIT', 'Input recognised; all subjects mode.')
                # Does the indir exist at all? If not - exit
                if not self.isdir(self.datain):
                    self.log_error('INIT', f'Exit Error. Input directory {self.datain} not found.')
                    return [False, f'Exit Error. Input directory not found {self.datain}.']
                else:
                    self.log_ok('INIT', 'Input directory found.')
                    # Now, do we have any subjects in the directory? If not - exit
                    allsubs = [f for f in self.ls(self.datain) if f.startswith('sub-') and self.isdir(self.join(self.datain, f))]
                    if len(allsubs) == 0:
                        self.log_error('INIT', f'Exit Error. No subjects found in {self.input}.')
                        return [False, f'Exit Error. No subjects found in the input directory {self.datain}.']
                    else:
                        # set as input
                        self.subs = allsubs
                        if self.verbose:
                            print(f'Found {len(allsubs)} subjects in the input directory: {self.datain}')
                        self.log_ok('INIT', f'Found {len(self.subs)} subjects in the input directory.')
                        return [True, f'Input recognised. All subjects mode. Found {len(allsubs)} subjects in the input directory {self.datain}.']
            else:
                self.log_error('INIT', 'Exit Error. Mode not recognised.')
                return [False, 'Exit Error. Mode not recognised.']
    
    def check_telegram(self):
        # Check if telegram setup file is present and whether the user wants to use it
        # Not critical so it does not return anything
        if self.exists('send_telegram.py') and self.telegram == True:
            self.telegram = True
            self.log_ok('INIT', 'Telegram setup file found.')
            if self.verbose:
                print('Telegram notifications are enabled')
            from send_telegram import sendtel
            self.tg = sendtel # use self.tg('msg') to send messages
        else:
            self.log_ok('INIT', 'Telegram setup file not found.')
            self.telegram = False
            if self.verbose:
                print('Telegram not available')
    
    def check_container(self):
        # Check if we are using dipy and fsl from the containers
        # When creating the container an empty file is created in the /opt folder
        # so we can check if the container is loaded by checking if the file exists
        
        if not self.exists('/opt/dwiprep.txt'):
            self.log_error('INIT', 'Not running in the container.')
            return [False, 'Exit error. Not running in required singularity image. Please ensure that the singularity image is loaded']
        else:
            if self.verbose:
                print('Singularity image loaded')
            self.log_ok('INIT', 'Singularity image loaded.')
            return [True, 'Singularity image loaded']

    def check_subid(self, sub):
        # Check if subject name contains sub- prefix
        # Can fix so no return value
        if not sub.startswith('sub-'):
            self.log_warning(f'{sub}', f'Subject name {sub} does not contain sub- prefix. Adding it.')
            sub = 'sub-' + sub
        return sub

    def check_subject_indir(self, sub):
        # Check if subject directory exists in indir
        if not self.exists(self.join(self.datain, sub)):
            print(f'Subject {sub} directory not found in {self.datain}')
            self.log_error(f'{sub}', f'Subject {sub} directory not found in {self.datain}')
            return [False, f'Subject {sub} directory not found in {self.datain}']
        else:
            if self.verbose:
                print(f'Subject {sub} directory found in {self.datain}')
            self.log_ok(f'{sub}', f'Subject {sub} directory found in {self.datain}')
            return [True, f'Subject {sub} directory found in {self.datain}']

    def check_tmp_dir(self):
        # Run once at the begging of each processing stage
        # Simple method to check if tmp folder exists
        # create it if it does not exist, but do not delete it
        # AND if mkdir fails, return False

        if not self.exists('tmp'):
            self.log_warning('INIT', 'tmp folder not found. Creating it...')
            try:
                self.mkdir('tmp')
                print('tmp folder created')
                self.log_ok('INIT', 'tmp folder created.')
                return [True, 'tmp folder created']
            except:
                self.log_error('INIT', 'tmp folder could not be created.')
                return [False, 'Exit error. Could not create tmp folder']
        else:
            self.log_ok('INIT', 'tmp folder found.')
            if self.verbose:
                print('tmp directory already exists')
            return [True, 'tmp directory already exists']

    def check_subject_tmpdir(self, sub):
        # Check if subject directory exists in tmp
        # Create it if it does not exist
        # delete it if it does exist and create it again
        # AND if mkdir fails, return False
        if not self.exists(self.join('tmp', sub)):
            self.log_info(f'{sub}', f'Subject {sub} directory not found in tmp. Creating it...')
            try:
                self.mkdir(self.join('tmp', sub))
                self.log_ok(f'{sub}', f'Subject {sub} directory created in tmp.')
                if self.verbose:
                    print(f'Subject {sub} directory created in tmp')
                return [True, f'Subject {sub} directory created in tmp']
            except:
                self.log_error(f'{sub}', f'Subject {sub} directory could not be created in tmp.')
                return [False, f'Exit error. Could not create subject {sub} directory in tmp']
        else:
            self.log_info(f'{sub}', f'Subject {sub} directory found in tmp.')
            if self.verbose:
                print(f'Subject {sub} directory found in tmp')
            # remove it 
            try:
                self.remove(self.join('tmp', sub))
                self.log_ok(f'{sub}', f'Subject {sub} directory removed from tmp.')
            except:
                self.log_error(f'{sub}', f'Subject {sub} directory could not be removed from tmp.')
                return [False, f'Exit error. Could not remove subject {sub} directory from tmp']

            # create it again
            try:
                self.mkdir(self.join('tmp', sub))
                self.log_ok(f'{sub}', f'Subject {sub} directory created in tmp.')
                return [True, f'Subject {sub} directory created in tmp']
            except:
                self.log_error(f'{sub}', f'Subject {sub} directory could not be created in tmp.')
                return [False, f'Exit error. Could not create subject {sub} directory in tmp']

    ########################################
    # Helping methods ######################
    ########################################

    def cp_rawdata(self, sub):
        # Copy raw data to tmp folder
        # Returns True or False depending on success and message for logging

        import shutil

        # get all dwi files for pp
        try:
            bfs = [f for f in self.ls(self.join(self.datain, sub, 'dwi')) if '.DS_' not in f]
        except:
            self.log_error(f'{sub}', f'cannot find dwi dir for the subject')
            return [False, f'Cannot find DWI dir for this subject']

        # get all _AP_ files
        fsdwi = [f for f in bfs if '_SBRef_' not in f and '_ADC_' not in f and '_TRACEW_' not in f and '_ColFA_' not in f and '_FA_' not in f]
        if len(fsdwi) != 6:
            print(f'{sub} has {len(fsdwi)} dwi files')
            self.log_error(f'{sub}', f'{sub} has {len(fsdwi)} dwi files and should have 6.')
            return [False, f'Number of dwi files is not 6, but {len(fsdwi)}']

        # cp dwi to tmp
        for f in fsdwi:
            if '_AP_' in f:
                fn = f'{sub}_AP.{f.split(".")[-1]}'
                if self.verbose:
                    print(f'cp {self.join(self.datain, sub, "dwi", f)} ---> {self.join("tmp", sub, fn)}')
                shutil.copy(self.join(self.datain, sub, "dwi", f), self.join("tmp", sub, fn))

            elif '_PA_' in f:
                fn = f'{sub}_PA.{f.split(".")[-1]}'
                if self.verbose:
                    print(f'cp {self.join(self.datain, sub, "dwi", f)} ---> {self.join("tmp", sub, fn)}')
                shutil.copy(self.join(self.datain, sub, "dwi", f), self.join("tmp", sub, fn))
            else:
                pass
            
            self.log_ok(f'{sub}', f'Copied raw data to tmp folder: {f}')
        return [True, f'Copied raw data for {sub} to tmp folder']

    def check_qa(self, dwi):
        
        # set of common methods for all QA things;
        # Check if the entire path exist to the qa folder
        # try to create it if not, but if that fails, try to create qadir in the current directory
        # but ask user if they want to do that, if not then set self.qadir to False and do not run QA

        # Then try to create all the other folders in the qadir; subs and plots. The latter should be created
        # with all the steps as subdirs.
        
        # If all is good this will stay True, if not it will be set to False
        # Furthermore, this is the first time this is set, so it has to be run to 
        # enable QA at all

        self.runqa = True
        self.log_info('QA', 'Checking if QA is enabled')

        if self.qadir is None:
            # QA not requested
            if self.verbose:
                print('QA not requested')
            self.log_info('QA', 'QA not requested')
            self.runqa = False
            return [False, 'QA not requested']
        else:
            if self.exists(self.qadir):
                if self.verbose:
                    self.log_info('QA', f'QA directory exists: {self.qadir}')
                    print(f'QA directory found: {self.qadir}')
                    # We may need to create the sub and plots dirs, so no return yet
            else:
                print(f'QA directory not found: {self.qadir}')
                self.log_info('QA', f'QA directory not found: {self.qadir}')
                createqadir = input('Do you want to try create it? [y/n]: ')
                if createqadir == 'y':
                    try:
                        self.makedirs(self.qadir)
                        print(f'QA directory created: {self.qadir}')
                        self.log_info('QA', f'QA directory created: {self.qadir}')
                        # We may need to create the sub and plots dirs, so no return yet
                    except:
                        print(f'Could not create QA directory: {self.qadir}.')
                        self.log_error('QA', f'Could not create QA directory: {self.qadir}.')
                        createinhere = input('Do you want to create it in the current directory? [y/n]: ')
                        if createinhere == 'y':
                            try:
                                # this will create directory in the current directory
                                # take last dirname from the path and try to create it
                                self.mkdir(self.split(self.qadir)[-1])
                                self.qadir = self.abspath(self.split(self.qadir)[-1])
                                print(f'QA directory created: {self.qadir}')
                                self.log_info('QA', f'QA directory created: {self.qadir}')

                            except:
                                # print('Could not create qa directory in current directory. QA will not be run.')
                                self.runqa = False
                                self.qadir = False
                                self.log_error('QA', 'Could not create qa directory in current directory. QA will not be run.')
                                return [False, 'Could not create qa directory in current directory. QA will not be run.']
                        else:
                            # print('No dir for QA so QA will not be run.')
                            self.runqa = False
                            self.qadir = False
                            self.log_error('QA', 'No dir for QA so QA will not be run.')
                            return [False, 'No dir for QA so QA will not be run.']
                else:
                    # print('No dir for QA so QA will not be run.')
                    self.runqa = False
                    self.qadir = False
                    self.log_error('QA', 'No dir for QA so QA will not be run.')
                    return [False, 'No dir for QA so QA will not be run.']

            # DWI structure
            if dwi:
                print('Requested to QA DWI data')
                self.log_info('QA', 'Requested to QA DWI data')
                # this indicates we are running QA on dwi data
                # check if the folder structure is correct for the data
                # That is:
                
                # Dirs to create:
                dwiqadirs = [self.join(self.qadir, 'dwi'),\
                self.join(self.qadir, 'dwi', 'subs'),\
                self.join(self.qadir, 'dwi', 'plots'),\
                self.join(self.qadir, 'dwi', 'plots', 'gibbs'),\
                self.join(self.qadir, 'dwi', 'plots', 'p2s'),\
                self.join(self.qadir, 'dwi', 'plots', 'topup'),\
                self.join(self.qadir, 'dwi', 'plots', 'eddy')]

                for d in dwiqadirs:
                    if not self.exists(d):
                        try:
                            self.mkdir(d)
                            self.log_info('QA', f'Created directory: {d}')
                        except:
                            self.log_error('QA', f'Could not create directory: {d}')
                            self.runqa = False
                            self.qadir = False
                            return [False, f'Could not create directory: {d}']
                    else:
                        self.log_info('QA', f'Directory exists: {d}')

            # if we got here, we are good to go
            self.log_ok('QA', 'QA directories found and created if needed, QA is enabled')
            return [True, 'QA directories found and created if needed']

    ########################################
    # Plotting methods #####################
    ########################################

    def gif_dwi_4d(self, sub, image, gif, title, slice=55, fdur=500):

        # Create a gif of a 4D image
        # It will go through the 4th dimension and create a gif, 
        # Plane is set as axial, slice is set to 55 by default
        # image: path to 4D image
        # gif: path to gif
        # title: title of gif
        # fdur: frame duration in ms
        # slice: slice to show

        import matplotlib.pyplot as plt
        from PIL import Image

        # TODO - SAVE to QA dir directly
        # Make gif of dwi data
        # Use self.qadir
        try:
            img, __ = self.load_nifti(image)
            self.log_info(f'{sub}', f'plotdwi4d: Loaded image: {image}')
        except:
            print(f'Could not load {image}')
            self.log_error(f'{sub}', f'plotdwi4d: Could not load {image}')
            return [False, 'cannot load image']

        # Need path to dump tmp images
        tmpDir = self.dirname(gif)

        # make gif
        if self.verbose:
            print(f'Extracting image slices from {image} and saving to {tmpDir}')
        for v in range(img.shape[-1]):
            fig, ax = plt.subplots(1,3, figsize=(15,5), subplot_kw=dict(xticks=[], yticks=[]))
            fig.subplots_adjust(hspace=0.25, wspace=0.25)
            fig.suptitle(f'{title}', fontsize=16)
            plt.tight_layout()
            ax.flat[0].imshow(img[:, :, slice, v].T, origin='lower', cmap='gray')
            ax.flat[1].imshow(img[:, slice, :, v].T, origin='lower', cmap='gray')
            ax.flat[2].imshow(img[slice, :, :, v].T, origin='lower', cmap='gray')
            
            fig.savefig(self.join(tmpDir, f'tmp_img{1000+v}.png'))
            plt.close(fig)

        # Make GIF
        if self.verbose:
            print(f'Making GIF from images in {tmpDir} and saving to {gif}')
        try:
            images = [Image.open(self.join(tmpDir, i)) for i in self.ls(self.join(tmpDir)) if i.endswith('.png') and i.startswith('tmp_')]
            image1 = images[0]
            image1.save(self.join(gif), format = "GIF", save_all=True, append_images=images[1:], duration=fdur, loop=0)
            self.log_info(f'{sub}', f'plotdwi4d: Made GIF: {gif}')
        except:
            print(f'Could not make GIF {gif} from images in {tmpDir}')
            self.log_error(f'{sub}', f'plotdwi4d: Could not make GIF {gif} from images in {tmpDir}')
            return [False, f'cannot make gif {gif}']
        
        # Clean up
        if self.verbose:
            print(f'Cleaning up {tmpDir}')
        try:
            for i in self.ls(self.join(tmpDir)):
                if i.endswith('.png') and i.startswith('tmp_img'):
                    self.remove(self.join(tmpDir, i))
            self.log_info(f'{sub}', f'plotdwi4d: Cleaned up {tmpDir}')
        except:
            print(f'Could not clean up {tmpDir}')
            self.log_error(f'{sub}', f'plotdwi4d: Could not clean up {tmpDir}')
            return [False, f'could not clean up tmpDir for {gif}']
        self.log_ok(f'{sub}', f'plotdwi4d: Made GIF: {gif}')
        return [True, f'GIF created: {gif}']

    def plt_compare_4d(self, file1, file2, out, sub=None, vols=[0], slice=[50,50,50], \
        cmap='gray', compare='sub'):

        # Plotting function that compares two 4D nifti files
        # file1 and file2 are the full paths to the files
        # sub is the subject ID
        # vols is a list of volumes to plot as a list of ints
        # slice is a list of slices to plot as a list of ints
        # cmap is the colormap to use
        # compare is either 'sub' or 'diff':
        #   if 'sub' then the two files are subtracted from each other
        #   if 'diff' then the two files are plotted side by side

        import matplotlib.pyplot as plt
        import numpy as np
        # Make plot of comparison between raw and processed data
        # TODO Use self.qadir
        
        if sub is None:
            # if no sub is specified, use the basename of the 1st file
            sub = self.split(file1)[-1].split('_')[0]

        try:
            # Load images
            img1, __ = self.load_nifti(file1)
            img2, __ = self.load_nifti(file2)
            self.log_info(f'{sub}', f'plt_compare_4d: Loaded images: {file1} and {file2}')
        except:
            print(f'Unable to load images for comparison: {file1} and {file2}')
            self.log_error(f'{sub}', f'plt_compare_4d: Unable to load images for comparison: {file1} and {file2}')
            return [False, f'Unable to load images for comparison: {file1} and {file2}']

        # Make plot
        # modify the file paths to get the plot titles
        img1_name = '_'.join(self.basename(file1).split('.')[0].split('_')[1:])
        img2_name = '_'.join(self.basename(file1).split('.')[0].split('_')[1:])

        for v in vols:
            # plotting for the images and difference
            fig, ax = plt.subplots(3,3, \
                subplot_kw = {'xticks':[], 'yticks':[]}, \
                sharex=True, sharey=True)
            fig.suptitle(f'{sub} v {v}', fontsize=16)
            
            # Order of plots goes row by row, plot each plane
            # Image 1
            ax.flat[0].imshow(img1[:,:,slice[0],v].T, cmap=cmap, origin='lower')
            ax.flat[0].set_title(img1_name)
            ax.flat[3].imshow(img1[:,slice[1],:,v].T, cmap=cmap, origin='lower')
            ax.flat[6].imshow(img1[slice[2],:,:,v].T, cmap=cmap, origin='lower')

            # Image 2
            ax.flat[1].imshow(img2[:,:,slice[0],v].T, cmap=cmap, origin='lower')
            ax.flat[1].set_title(img2_name)
            ax.flat[4].imshow(img2[:,slice[1],:,v].T, cmap=cmap, origin='lower')
            ax.flat[7].imshow(img2[slice[2],:,:,v].T, cmap=cmap, origin='lower')

            if compare == 'res':
                ax.flat[2].imshow(np.sqrt(img1[:,:,slice[0],v].T - img2[:,:,slice[0],v].T)**2, cmap=cmap, origin='lower')
                ax.flat[2].set_title('Difference')
                ax.flat[5].imshow(np.sqrt(img1[:,slice[1],:,v].T - img2[:,slice[1],:,v].T)**2, cmap=cmap, origin='lower')
                ax.flat[8].imshow(np.sqrt(img1[slice[2],:,:,v].T - img2[slice[2],:,:,v].T)**2, cmap=cmap, origin='lower')
            elif compare == 'sub':
                ax.flat[2].imshow(img1[:,:,slice[0],v].T - img2[:,:,slice[0],v].T, cmap=cmap, origin='lower')
                ax.flat[2].set_title('Difference')
                ax.flat[5].imshow(img1[:,slice[1],:,v].T - img2[:,slice[1],:,v].T, cmap=cmap, origin='lower')
                ax.flat[8].imshow(img1[slice[2],:,:,v].T - img2[slice[2],:,:,v].T, cmap=cmap, origin='lower')
            else:
                print('Invalid comparison type')
                self.log_error(f'{sub}', f'plt_compare_4d: Invalid comparison type: {compare}')
                return [False, 'Invalid comparison type']

            plt.tight_layout()
            fig.savefig(out + f'_{v}.png', dpi=300)
            plt.close(fig)

        self.log_ok(f'{sub}', f'plt_compare_4d: Made plots for {file1} and {file2}')
        return [True, f'Comparison plots created for {sub}']

    ########################################
    # DWI Preprocessing ####################
    ########################################

    def gibbs(self):
        
        # Check if QA required
        # This has been disabled as there was a problem with the QApath
        # also, did not want to spend too much time on it. 
        # plots are being created but not being moved the the QA dir, this can be done later.
        
        # Check if we have subjects to process
        print(f'{len(self.subs)} subjects to process')
        self.log_info('INIT', f'{len(self.subs)} subjects to process for gibbs ringing correction, taks name: {self.task}')

        # dump the list of subjects to process to a file
        self.log_subdump(self.subs)

        # Loop over subjects
        for i, sub in enumerate(self.subs):

            if self.exists(self.join(self.dataout, sub)):
                self.log_warning(f'{sub}', f'gibbs: Output directory already exists, skipping subject')
                print(f'Output directory already exists, skipping subject: {sub}')
                continue

            print(f'Processing subject {sub} ({i+1}/{len(self.subs)} for {self.gibbs_method} gibbs ringing correction)')
            
            # Log start
            self.log_subjectStart(sub, f'{self.gibbs_method}gibbs')

            # Perform subject checks
            # Check indir
            s, m = self.check_subject_indir(sub)
            if not s:
                self.log_error(sub, m)
                print(m)
                self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')
                continue
            else:
                self.log_ok(sub, m)
                pass

            # Check if we have the subdir in tmp
            s, m = self.check_subject_tmpdir(sub)
            if not s:
                self.log_error(sub, m)
                print(m)
                self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')
                continue
            else:
                self.log_ok(sub, m)
                pass
            
            # Copy the data
            s, m = self.cp_rawdata(sub)
            if not s:
                self.log_error(sub, m)
                print(m)
                self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')
                continue
            else:
                self.log_ok(sub, m)
                pass


            # run depending on method selected
            ap_in = self.join("tmp", sub, sub + "_AP.nii")
            ap_out= self.join("tmp", sub, sub + "_AP_gib.nii.gz")
            pa_in = self.join("tmp", sub, sub + "_PA.nii")
            pa_out= self.join("tmp", sub, sub + "_PA_gib.nii.gz")

            if self.gibbs_method == 'dipy':
                self.log_info(f'{sub}', f'Running {self.gibbs_method}gibbs ringing correction for AP {sub}')
                self.sp.run(f'dipy_gibbs_ringing {ap_in} --out_unring {ap_out} --num_processes={self.threads}', shell=True)
                self.log_info(f'{sub}', f'Running {self.gibbs_method}gibbs ringing correction for PA {sub}')
                self.sp.run(f'dipy_gibbs_ringing {pa_in} --out_unring {pa_out} --num_processes={self.threads}', shell=True)

            elif self.gibbs_method == 'mrtrix3':
                self.log_info(f'{sub}', f'Running {self.gibbs_method}gibbs ringing correction for AP {sub}')
                self.sp.run(f'mrdegibbs {ap_in} {ap_out} -nthreads {self.threads}', shell=True)
                self.log_info(f'{sub}', f'Running {self.gibbs_method}gibbs ringing correction for PA {sub}')
                self.sp.run(f'mrdegibbs {pa_in} {pa_out} -nthreads {self.threads}', shell=True)

            # QA
            # create a directory for the QA plots
            self.mkdir(self.join('tmp', sub, 'imgs'))
            self.mkdir(self.join('tmp', sub, 'imgs', 'gibbs'))
            # make gif, AP raw
            i = self.join("tmp", sub, f"{sub}_AP.nii")
            g = self.join("tmp", sub, "imgs", "gibbs", f"{sub}_AP_raw.gif")
            self.gif_dwi_4d(sub=sub, image=i, gif=g, title=f'{sub} ap raw')
            # make gif, AP gib
            i = self.join("tmp", sub, f"{sub}_AP_gib.nii.gz")
            g = self.join("tmp", sub, "imgs", "gibbs", f"{sub}_AP_gib.gif")
            self.gif_dwi_4d(sub=sub, image=i, gif=g, title=f'{sub} ap gib')
            
            # compare volumes
            v1 = self.join("tmp", sub, sub + "_AP.nii")
            v2 = self.join("tmp", sub, sub + "_AP_gib.nii.gz")
            oo = self.join("tmp", sub, "imgs", "gibbs", f"{sub}_AP_compare_raw_gibbs")
            self.plt_compare_4d(file1=v1, file2=v2, sub=sub, out=oo, vols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

            # copy output to dataout folder
            if self.copy:
                try:
                    #self.copytree(self.join('tmp', sub), self.join(self.dataout, sub))
                    self.sp.run(f"cp -r {self.join('tmp', sub)} {self.join(self.dataout, sub)}", shell=True)
                    self.log_ok(f'{sub}', f'Copied {sub} to {self.dataout}')
                except:
                    self.log_error(f'{sub}', f'Could not copy data to dataout folder: {self.dataout}')
                    print(f'Could not copy data to dataout folder')
                    self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')
                    continue
            
            if self.clean:
                try:
                    self.sp.run(f'rm -rf {self.join("tmp", sub)}', shell=True)
                    self.log_ok(f'{sub}', f'Removed tmp folder for {sub}')
                except:
                    self.log_error(f'{sub}', f'Could not remove tmp folder for {sub}')
                    print(f'Could not remove tmp folder for {sub}')
                    self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')
                    continue

            self.log_ok(f'{sub}', f'Gibbs ringing correction {self.gibbs_method} for {sub} completed successfully')
            self.log_subjectEnd(sub, f'{self.gibbs_method}gibbs')

        # Loop end
        if self.telegram:
            self.log_ok('ALL', f'Gibbs ringing correction completed successfully for {len(self.subs)} subjects')
            self.tg(f'Gibbs ringing correction completed for all {len(self.subs)} subjects')
         
    def mppca(self, skip_processed):
        # Quicker and less aggressive denoising method implemented in mrtrix3
        # https://mrtrix.readthedocs.io/en/latest/reference/commands/mppca.html

        # skip_processed if True it will check if the subject has been processed and skip it
        # specifically it will ceck for AP and PA nii.gz file with mppca in the name
        # May want to adjust the skip_processed to check for specific filename, which depends on preprocessing steps.

        from dipy.denoise.noise_estimate import estimate_sigma
        import matplotlib.pyplot as plt
        import numpy as np

        print(f'{len(self.subs)} subjects to process')
        self.log_info('ALL', f'Running mrtrix3_mppca denoising for {len(self.subs)} subjects')
        self.log_subdump(self.subs)

        # Loop over subjects
        for i, sub in enumerate(self.subs): 

            if skip_processed:
                if self.exists(self.join(self.dataout, sub, sub + '_AP_gib_mppca.nii.gz')) and self.exists(self.join(self.dataout, sub, sub + '_PA_gib_mppca.nii.gz')):
                    self.log_ok(f'{sub}', f'Subject {sub} already processed, skipping subject')
                    print(f'{sub} {i+1} out of {len(self.subs)} - already processed, skipping')
                    continue
            
            print(f'\n{sub} {i+1} out of {len(self.subs)} - processing')
            # Run mppca denoise
            # if dir exists in derivatives

            # Log start
            self.log_subjectStart(sub, 'mrtrix3_mppca')

            if not self.exists(self.join(self.dataout, sub)):
                self.log_warning(f'{sub}', f'mrtrix3_mppca: Output directory does not exist, skipping subject')
                print(f'Output directory does not exist, skipping subject: {sub}')
                self.log_subjectEnd(sub, 'mrtrix3_mppca')
                continue
            
            # make tmp dirs
            self.mkdir(self.join('tmp', sub))
            self.mkdir(self.join('tmp', sub, 'imgs'))
            self.mkdir(self.join('tmp', sub, 'imgs', 'mrtrix3_mppca'))
            self.mkdir(self.join('tmp', sub, 'sigma_noise'))

            # copy required files
            files = ['_AP_gib.nii.gz', '_PA_gib.nii.gz', '_AP.nii', '_PA.nii', '_AP.bval', '_AP.bvec']    
            for f in files:
                try:
                    self.copyfile(self.join(self.dataout, sub, sub+f), self.join('tmp', sub, sub+f))
                    self.log_ok(f'{sub}', f'mrtrix3_mppca: Copied {sub+f} to tmp folder')
                except:
                    self.log_error(f'{sub}', f'mrtrix3_mppca: Could not copy file {f}')
                    print(f'Could not copy file {f}')
                    self.log_subjectEnd(sub, 'mrtrix3_mppca')
                    continue

            # Load data, raw and gibbs
            # Load raw for sigma estimation
            try:
                ap_raw, __ = self.load_nifti(self.join('tmp', sub, sub + '_AP.nii'))
                pa_raw, __ = self.load_nifti(self.join('tmp', sub, sub + '_PA.nii'))
                # Load gibbs, for sigma and mppca
                ap_gib, __ = self.load_nifti(self.join('tmp', sub, sub + '_AP_gib.nii.gz'))
                pa_gib, __ = self.load_nifti(self.join('tmp', sub, sub + '_PA_gib.nii.gz'))
                ap_bval = np.loadtxt(self.join('tmp', sub, sub + '_AP.bval'))
                pa_bval = np.array([5.,5.,5.,5.,5.])
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: Could not load data')
                print(f'{sub} Could not load data')
                self.log_subjectEnd(sub, 'mrtrix3_mppca')
                continue

            # Estimate sigma for raw volumes
            try:
                s_ap_raw = estimate_sigma(ap_raw, N = self.n_coils)
                s_pa_raw = estimate_sigma(pa_raw, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_raw_sigma.npy'), s_ap_raw)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_raw_sigma.npy'), s_pa_raw)
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: Could not estimate sigma for raw volumes')
                print(f'{sub} Could not estimate sigma for raw volumes')
                self.log_subjectEnd(sub, 'mrtrix3_mppca')
                continue

            # Estimate sigma for gibbs volumes
            try:
                s_ap_gib = estimate_sigma(ap_gib, N = self.n_coils)
                s_pa_gib = estimate_sigma(pa_gib, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_gib_sigma.npy'), s_ap_gib)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_gib_sigma.npy'), s_pa_gib)
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: Could not estimate sigma for gibbs volumes')
                print(f'{sub} Could not estimate sigma for gibbs volumes')
                self.log_subjectEnd(sub, 'mrtrix3_mppca')
                continue
            
            # run mrtrix3_mppca
            for d in ['AP', 'PA']:
                try:
                    # run mrtrix3_mppca
                    iin = self.join("tmp", sub, sub+f"_{d}_gib.nii.gz")
                    out = self.join("tmp", sub, sub+f"_{d}_gib_mppca.nii.gz")
                    noise = self.join("tmp", sub, "imgs", "mrtrix3_mppca", sub+f"_{d}_mppca_noise.nii.gz")
                    resid = self.join("tmp", sub, "imgs", "mrtrix3_mppca", sub+f"_{d}_mppca_resid.nii.gz")
                    
                    self.sp.run(f'dwidenoise -nthreads {self.threads} {iin} {out} -noise {noise}', shell=True)
                    self.sp.run(f'mrcalc {iin} {out} -subtract {resid}', shell=True)
                    self.log_ok(f'{sub}', f'mrtrix3_mppca: {d} completed successfully')
                except:
                    self.log_error(f'{sub}', f'mrtrix3_mppca: {d} failed')
                    print(f'{sub} {d} mrtrix3_mppca failed')
                    continue
            
            # estimate sigma for AP and PA
            try:
                ap_mppca, __ = self.load_nifti(self.join('tmp', sub, sub + '_AP_gib_mppca.nii.gz'))
                pa_mppca, __ = self.load_nifti(self.join('tmp', sub, sub + '_PA_gib_mppca.nii.gz'))
                s_ap_mppca = estimate_sigma(ap_mppca, N = self.n_coils)
                s_pa_mppca = estimate_sigma(pa_mppca, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_gib_mppca_sigma.npy'), s_ap_mppca)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_gib_mppca_sigma.npy'), s_pa_mppca)
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: Could not estimate sigma for mrtrix3_mppca volumes')
                print(f'{sub} Could not estimate sigma for mrtrix3_mppca volumes')
                self.log_subjectEnd(sub, 'mrtrix3_mppca')
                continue
            
            
            self.log_info(f'{sub}', f'mrtrix3_mppca: plotting all volumes')
            # plot volumes - noise residuals
            xcmp = 'gray'
            try:
                for d in ['AP', 'PA']:

                    if d == 'AP':
                        bvl = ap_bval
                        gib = ap_gib
                        raw = ap_raw
                        mpp = ap_mppca
                        sgib = s_ap_gib
                        sraw = s_ap_raw
                        smpp = s_ap_mppca
                        resi, __ = self.load_nifti(self.join("tmp", sub, "imgs", "mrtrix3_mppca", sub+"_AP_mppca_resid.nii.gz"))
                    else:
                        bvl = pa_bval
                        gib = pa_gib
                        raw = pa_raw
                        mpp = pa_mppca
                        sgib = s_pa_gib
                        sraw = s_pa_raw
                        smpp = s_pa_mppca
                        resi, __ = self.load_nifti(self.join("tmp", sub, "imgs", "mrtrix3_mppca", sub+"_PA_mppca_resid.nii.gz"))

                    # Take the middle slice in all dimensions of an image
                    d0 = round(raw.shape[0]/2)
                    d1 = round(raw.shape[1]/2)
                    d2 = round(raw.shape[2]/2)

                    for i, vs in enumerate(range(0, raw.shape[3])):

                        # computes the residuals
                        #rms_gibmppca = np.sqrt(abs((gib[:,:,s,vs] - mpp[:,:,s,vs]) ** 2))
                        #rms_rawmppca = np.sqrt(abs((raw[:,:,s,vs] - mpp[:,:,s,vs]) ** 2))

                        fig1, ax = plt.subplots(4, 3, figsize=(6, 8), subplot_kw={'xticks': [], 'yticks': []})
                    
                        fig1.subplots_adjust(hspace=0.05, wspace=0.10)
                        fig1.suptitle(f'{sub} {d} vol={vs} bval={int(bvl[i])}', fontsize=15)

                        # Raw image
                        ax.flat[0].imshow(raw[d0,:,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[1].imshow(raw[:,d1,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[1].set_title('Raw, ' + r'$\sigma_{noise}$' + f' = {round(sraw[i])}')
                        ax.flat[2].imshow(raw[:,:,d2,vs].T, cmap=xcmp, interpolation='none',origin='lower')

                        # Gibbs image
                        ax.flat[3].imshow(gib[d0,:,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[4].imshow(gib[:,d1,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[4].set_title('Gibbs, ' + r'$\sigma_{noise}$' + f' = {round(sgib[i])}')
                        ax.flat[5].imshow(gib[:,:,d2,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        
                        # mppca image
                        ax.flat[6].imshow(mpp[d0,:,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[7].imshow(mpp[:,d1,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[7].set_title('MPPCA, ' + r'$\sigma_{noise}$' + f' = {round(smpp[i])}')
                        ax.flat[8].imshow(mpp[:,:,d2,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        
                        # Residuals GIBBS - MPPCA
                        ax.flat[9].imshow(resi[d0,:,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[10].imshow(resi[:,d1,:,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        ax.flat[10].set_title('Resid Gibbs - MPPCA')
                        ax.flat[11].imshow(resi[:,:,d2,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                        
                        sfig = self.join('tmp', sub, 'imgs', 'mrtrix3_mppca', f'{sub}_{d}_v-{1000+int(vs)}.png')
                        fig1.savefig(sfig)

                        plt.close()
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: error while plotting volumes')
                print(f'{sub} Error while plotting volumes')


            # Plot the noise residuals
            self.log_info(f'{sub}', f'mrtrix3_mppca: plotting noise')
            try:
                for d in ['AP', 'PA']:
                    fig0, ax = plt.subplots(1, 3 , figsize = (6,2), subplot_kw={'xticks': [], 'yticks': []})
                    fig0.subplots_adjust(hspace=0.05, wspace=0.05)
                    fig0.suptitle(f'{sub} {d} MPPCA noise', fontsize=15)

                    mppca, __ = self.load_nifti(self.join("tmp", sub, "imgs", "mrtrix3_mppca", sub+f"_{d}_mppca_noise.nii.gz"))
                    
                    # Plot the noise residuals
                    ax.flat[0].imshow(mppca[d0,:,:].T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[1].imshow(mppca[:,d1,:].T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[2].imshow(mppca[:,:,d2].T, cmap=xcmp, interpolation='none',origin='lower')

                    sfig0 = self.join('tmp', sub, 'imgs', 'mrtrix3_mppca', f'{sub}_{d}_noise.png')
                    fig0.savefig(sfig0)
                    plt.close()
            except:
                self.log_error(f'{sub}', f'mrtrix3_mppca: error while plotting noise')
                print(f'{sub} Error while plotting noise')

            self.log_ok(f'{sub}', f'mrtrix3_mppca: plotting completed')
            
            # move all files to derivatives
            if self.copy:
                self.log_info(f'{sub}', f'mrtrix3_mppca: copying files to derivatives')
                try:
                    # yet again the shutil copy fails me, fallback to the cp method
                    for file in ['_AP_gib_mppca.nii.gz', '_PA_gib_mppca.nii.gz']:
                        self.sp.run(f'cp {self.join("tmp", sub, sub+file)} {self.join(self.dataout, sub, sub+file)}', shell=True)
                        self.log_ok(f'sub', f'mrtrix3_mppca: copied {sub+file} to {self.dataout}')

                    self.sp.run(f'cp -r {self.join("tmp", sub, "imgs", "mrtrix3_mppca")} {self.join(self.dataout, sub, "imgs")}', shell=True)
                    self.sp.run(f'cp -r {self.join("tmp", sub, "sigma_noise")} {self.join(self.dataout, sub)}', shell=True)
                    self.log_ok(f'{sub}', f'mrtrix3_mppca: all files copied to derivatives')
                except:
                    self.log_error(f'{sub}', f'mrtrix3_mppca: files not copied to derivatives')
                    print(f'{sub} files not copied to derivatives')
                    self.log_subjectEnd(sub, 'mrtrix3_mppca')
                    continue

            if self.clean:
                self.log_info(f'{sub}', f'mrtrix3_mppca: cleaning tmp folder')
                try:
                    #self.rmtree(self.join('tmp', sub))
                    self.sp.run(f'rm -rf {self.join("tmp", sub)}', shell=True)
                    self.log_ok(f'{sub}', f'mrtrix3_mppca: tmp folder cleaned')
                except:
                    self.log_error(f'{sub}', f'mrtrix3_mppca: tmp folder not cleaned')
                    print(f'{sub} tmp folder not cleaned')
                    self.log_subjectEnd(sub, 'mrtrix3_mppca')
                    continue

            self.log_subjectEnd(sub, 'mrtrix3_mppca')
        
        if self.telegram:
            self.log_ok('ALL', f'mrtrix3_mppca completed successfully for {len(self.subs)} subjects')
            self.tg(f'mrtrix3_mppca completed for all {len(self.subs)} subjects')

    def patch2self(self):
        # Runs patch to self denoising on the data
        # TODO implement subject skipp is processed. Look for AP, PA file with p2s in the name

        from dipy.core.gradients import gradient_table
        from dipy.denoise.patch2self import patch2self
        from dipy.denoise.noise_estimate import estimate_sigma
        # from dipy.denoise.denspeed import determine_num_threads
        import matplotlib.pyplot as plt
        import numpy as np
        from fun.eta import Eta # this takes around a week on a 80 thread meachine and 300 subs

        # set number of threads
        # determine_num_threads(self.threads)
        
        # Check if we have subjects to process
        print(f'{len(self.subs)} subjects to process')
        self.log_info('INIT', f'{len(self.subs)} subjects to process for patch2self denoise, taks name: {self.task}')

        # Loop over subjects
        # dump the list of subjects to process to a file
        self.log_subdump(self.subs)

        # Timer and ETA
        eta_p2s = Eta(mode='median', N = len(self.subs))

        # Loop over subjects
        for i, sub in enumerate(self.subs): 

            # Run patch2self
            # if dir exists in derivatives

            # Log start
            self.log_subjectStart(sub, 'dipyp2s')

            if not self.exists(self.join(self.dataout, sub)):
                self.log_warning(f'{sub}', f'patch2self: Output directory does not exist, skipping subject')
                print(f'Output directory does not exist, skipping subject: {sub}')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            # Timer update, return ETA to log
            self.log_info(sub, eta_p2s.update())
            # make tmp dirs
            self.mkdir(self.join('tmp', sub))
            self.mkdir(self.join('tmp', sub, 'imgs'))
            self.mkdir(self.join('tmp', sub, 'imgs', 'patch2self'))
            self.mkdir(self.join('tmp', sub, 'sigma_noise'))

            # copy required files
            files = ['_AP.bval', '_AP.bvec', '_AP_gib.nii.gz', '_PA_gib.nii.gz', '_AP.json', '_AP.nii', '_PA.nii']    
            for f in files:
                try:
                    self.copyfile(self.join(self.dataout, sub, sub+f), self.join('tmp', sub, sub+f))
                    self.log_ok(f'{sub}', f'patch2self: Copied {sub+f} to tmp folder')
                except:
                    self.log_error(f'{sub}', f'patch2self: Could not copy file {f}')
                    print(f'Could not copy file {f}')
                    self.log_subjectEnd(sub, 'dipyp2s')
                    continue

            # Load gradient table
            try:
                gtab = gradient_table(self.join('tmp', sub, sub + '_AP.bval'), self.join('tmp', sub, sub + '_AP.bvec'))
                txt = f'bvals shape {gtab.bvals.shape}, min = {gtab.bvals.min()}, max = {gtab.bvals.max()} with {len(np.unique(gtab.bvals))} unique values: {np.unique(gtab.bvals)}bvecs shape {gtab.bvecs.shape}, min = {gtab.bvecs.min()}, max = {gtab.bvecs.max()}'
                self.log_info(f'{sub}', f'patch2self: {txt}')
                # save b0s mask as numpy array  - which volumes are b0 in AP (bool)
                np.save(self.join('tmp', sub, f'{sub}_AP_b0mask.npy'), gtab.b0s_mask)
            except:
                self.log_error(f'{sub}', f'patch2self: Could not load gradient table')
                print(f'{sub} Could not load gradient table')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            # Load data, raw and gibbs
            # Load raw for sigma estimation
            try:
                ap_raw, __ = self.load_nifti(self.join('tmp', sub, sub + '_AP.nii'))
                pa_raw, __ = self.load_nifti(self.join('tmp', sub, sub + '_PA.nii'))
                # Load gibbs, for sigma and patch2self
                ap_gib, ap_gib_aff = self.load_nifti(self.join('tmp', sub, sub + '_AP_gib.nii.gz'))
                pa_gib, pa_gib_aff = self.load_nifti(self.join('tmp', sub, sub + '_PA_gib.nii.gz'))
                ap_bval = np.loadtxt(self.join('tmp', sub, f'{sub}_AP.bval'))
                pa_bval = np.array([5.,5.,5.,5.,5.])
            except:
                self.log_error(f'{sub}', f'patch2self: Could not load data')
                print(f'{sub} Could not load data')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue

            # Estimate sigma for raw volumes
            try:
                s_ap_raw = estimate_sigma(ap_raw, N = self.n_coils)
                s_pa_raw = estimate_sigma(pa_raw, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_raw_sigma.npy'), s_ap_raw)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_raw_sigma.npy'), s_pa_raw)
            except:
                self.log_error(f'{sub}', f'patch2self: Could not estimate sigma for raw volumes')
                print(f'{sub} Could not estimate sigma for raw volumes')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue

            # Estimate sigma for gibbs volumes
            try:
                s_ap_gib = estimate_sigma(ap_gib, N = self.n_coils)
                s_pa_gib = estimate_sigma(pa_gib, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_gib_sigma.npy'), s_ap_gib)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_gib_sigma.npy'), s_pa_gib)
            except:
                self.log_error(f'{sub}', f'patch2self: Could not estimate sigma for gibbs volumes')
                print(f'{sub} Could not estimate sigma for gibbs volumes')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            # run patch2self on AP
            try:
                ap_p2s = patch2self(ap_gib, ap_bval, model='ols', shift_intensity=True, \
                    clip_negative_vals=False, b0_threshold=50, verbose=True)
                self.log_ok(f'{sub}', f'patch2self: AP patch2self completed successfully')
            except:
                self.log_error(f'{sub}', f'patch2self: AP patch2self failed')
                print(f'{sub} AP patch2self failed')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            # run patch2self on PA
            try:
                pa_p2s = patch2self(pa_gib, pa_bval, model='ols', shift_intensity=True, \
                    clip_negative_vals=False, b0_threshold=50, verbose=True)
                self.log_ok(f'{sub}', f'patch2self: PA patch2self completed successfully')
            except:
                self.log_error(f'{sub}', f'patch2self: PA patch2self failed')
                print(f'{sub} PA patch2self failed')
                continue
            
            # estimate sigma for AP and PA
            try:
                s_ap_p2s = estimate_sigma(ap_p2s, N = self.n_coils)
                s_pa_p2s = estimate_sigma(pa_p2s, N = self.n_coils)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_AP_p2s_sigma.npy'), s_ap_p2s)
                np.save(self.join('tmp', sub, 'sigma_noise', f'{sub}_PA_p2s_sigma.npy'), s_pa_p2s)
            except:
                self.log_error(f'{sub}', f'patch2self: Could not estimate sigma for patch2self volumes')
                print(f'{sub} Could not estimate sigma for patch2self volumes')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            # save denoised vols
            # AP
            try:
                self.save_nifti(self.join('tmp', sub, sub+'_AP_p2s.nii.gz'), ap_p2s, ap_gib_aff)
                self.log_ok(f'{sub}', f'patch2self: AP patch2self saved successfully')
            except:
                self.log_error(f'{sub}', f'patch2self: AP patch2self save failed')
                print(f'{sub} AP patch2self save failed')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            # PA
            try:
                self.save_nifti(self.join('tmp', sub, sub+'_PA_p2s.nii.gz'), pa_p2s, pa_gib_aff)
                self.log_ok(f'{sub}', f'patch2self: PA patch2self saved successfully')
            except:
                self.log_error(f'{sub}', f'patch2self: PA patch2self save failed')
                print(f'{sub} PA patch2self save failed')
                self.log_subjectEnd(sub, 'dipyp2s')
                continue
            
            self.log_info(f'{sub}', f'patch2self: plotting all volumes')
            # plot volumes - noise residuals
            xcmp = 'gray'
            s = 42
            for d in ['AP', 'PA']:

                if d == 'AP':
                    bvl = ap_bval
                    gib = ap_gib
                    raw = ap_raw
                    p2s = ap_p2s
                    sgib = s_ap_gib
                    sraw = s_ap_raw
                    sp2s = s_ap_p2s
                else:
                    bvl = pa_bval
                    gib = pa_gib
                    raw = pa_raw
                    p2s = pa_p2s
                    sgib = s_pa_gib
                    sraw = s_pa_raw
                    sp2s = s_pa_p2s


                for i, vs in enumerate(range(0, raw.shape[3])):

                    # computes the residuals
                    rms_gibp2s = np.sqrt(abs((gib[:,:,s,vs] - p2s[:,:,s,vs]) ** 2))
                    rms_rawp2s = np.sqrt(abs((raw[:,:,s,vs] - p2s[:,:,s,vs]) ** 2))

                    fig1, ax = plt.subplots(2, 3, figsize=(12, 12),subplot_kw={'xticks': [], 'yticks': []})
                
                    fig1.subplots_adjust(hspace=0.05, wspace=0.05)
                    fig1.suptitle(f'{sub} {d} vol={vs} bval={int(bvl[i])}', fontsize =20)

                    # Raw image
                    ax.flat[0].imshow(raw[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[0].set_title('Raw, ' + r'$\sigma_{noise}$' + f' = {round(sraw[i])}')
                    # Gibbs image
                    ax.flat[1].imshow(gib[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[1].set_title('Gibbs, ' + r'$\sigma_{noise}$' + f' = {round(sgib[i])}')
                    # p2s image
                    ax.flat[2].imshow(p2s[:,:,s,vs].T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[2].set_title('P2S, ' + r'$\sigma_{noise}$' + f' = {round(sp2s[i])}')
                    # Raw - p2s
                    ax.flat[3].imshow(rms_rawp2s.T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[3].set_title('Raw - P2S')
                    # Gibbs - p2s
                    ax.flat[4].imshow(rms_gibp2s.T, cmap=xcmp, interpolation='none',origin='lower')
                    ax.flat[4].set_title('Gibbs - P2S')
                    
                    sfig = self.join('tmp', sub, 'imgs', 'patch2self', f'{sub}_{d}_v-{1000+int(vs)}.png')
                    fig1.savefig(sfig)

                    plt.close()

            self.log_ok(f'{sub}', f'patch2self: plotting all volumes completed successfully')
            # move all files to derivatives
            if self.copy:
                self.log_info(f'{sub}', f'patch2self: copying files to derivatives')
                try:
                    # yet again the shutil copy fails me, fallback to the cp method
                    for file in ['_AP_p2s.nii.gz', '_PA_p2s.nii.gz', '_AP_b0mask.npy']:
                        self.sp.run(f'cp {self.join("tmp", sub, sub+file)} {self.join(self.dataout, sub, sub+file)}', shell=True)
                        self.log_ok(f'sub', f'patch2self: copied {sub+file} to {self.dataout}')

                    self.sp.run(f'cp -r {self.join("tmp", sub, "imgs", "patch2self")} {self.join(self.dataout, sub, "imgs")}', shell=True)
                    self.sp.run(f'cp -r {self.join("tmp", sub, "sigma_noise")} {self.join(self.dataout, sub)}', shell=True)
                    self.log_ok(f'{sub}', f'patch2self: all files copied to derivatives')
                except:
                    self.log_error(f'{sub}', f'patch2self: files not copied to derivatives')
                    print(f'{sub} files not copied to derivatives')
                    self.log_subjectEnd(sub, 'dipyp2s')
                    continue

            if self.clean:
                self.log_info(f'{sub}', f'patch2self: cleaning tmp folder')
                try:
                    #self.rmtree(self.join('tmp', sub))
                    self.sp.run(f'rm -rf {self.join("tmp", sub)}', shell=True)
                    self.log_ok(f'{sub}', f'patch2self: tmp folder cleaned')
                except:
                    self.log_error(f'{sub}', f'patch2self: tmp folder not cleaned')
                    print(f'{sub} tmp folder not cleaned')
                    self.log_subjectEnd(sub, 'dipyp2s')
                    continue

            self.log_subjectEnd(sub, 'dipyp2s')
        
        if self.telegram:
            self.log_ok('ALL', f'Patch2Self completed successfully for {len(self.subs)} subjects')
            self.tg(f'Patch2Self completed for all {len(self.subs)} subjects')

    def topup(self, skip_processed):

        import json
        import matplotlib.pyplot as plt
        #from fun.eta import Eta
        from dipy.core.gradients import gradient_table

        # Runs FSL topup via subprocess
        # https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup

        # Check if we have subjects to process
        print(f'{len(self.subs)} subjects to process')
        self.log_info('INIT', f'{len(self.subs)} subjects to process for topup estimation taks name: {self.task}')

        # Loop over subjects
        # dump the list of subjects to process to a file
        self.log_subdump(self.subs)

        # Loop over subjects
        for i, sub in enumerate(self.subs): 

            # set acqparams file, we will check if it exists and skip if it does
            acqpar = self.join("tmp", sub, f"{sub}_acqparams.txt")

            if skip_processed:
                if self.exists(self.join(self.dataout, sub, sub + '_acqparams.txt')):
                    self.log_ok(f'{sub}', f'Subject {sub} already processed, skipping subject')
                    print(f'{sub} {i+1} out of {len(self.subs)} - already processed, skipping')
                    continue

            print(f'{sub} {i+1} out of {len(self.subs)} - processing')

            # Log start
            self.log_subjectStart(sub, 'topup')

            if not self.exists(self.join(self.dataout, sub)):
                self.log_warning(f'{sub}', f'topup: Output directory does not exist, skipping subject')
                print(f'Output directory does not exist, skipping subject: {sub}')
                self.log_subjectEnd(sub, 'topup')
                continue
            
            # make tmp dirs
            self.mkdir(self.join('tmp', sub))
            # self.mkdir(self.join('tmp', sub, 'imgs'))
            # self.mkdir(self.join('tmp', sub, 'imgs', 'topup'))

            # copy required files
            files = ['_AP_gib_mppca.nii.gz', '_PA_gib_mppca.nii.gz', '_AP.json', '_PA.json', '_AP.bval', '_AP.bvec']    
            for f in files:
                try:
                    self.copyfile(self.join(self.dataout, sub, sub+f), self.join('tmp', sub, sub+f))
                    self.log_ok(f'{sub}', f'topup: Copied {sub+f} to tmp folder')
                except:
                    self.log_error(f'{sub}', f'topup: Could not copy file {f}')
                    print(f'Could not copy file {f}')
                    self.log_subjectEnd(sub, 'topup')
                    continue
            
            # create acqparams.txt for topup
            # 0 1 0 TotalReadoutTime AP
            # 0 -1 0 TotalReadoutTime PA
            try:
                # Create b0 mask
                gtab = gradient_table(f'tmp/{sub}/{sub}_AP.bval', f'tmp/{sub}/{sub}_AP.bvec')
            except:
                self.log_error(f'{sub}', f'topup: Could not create gradient table')
                print(f'{sub} Could not create gradient table')
                self.log_subjectEnd(sub, 'topup')
                continue

            # Extract b0s
            apim = self.join('tmp', sub, sub+'_AP_gib_mppca.nii.gz')
            paim = self.join('tmp', sub, sub+'_PA_gib_mppca.nii.gz')
            apb0 = self.join('tmp', sub, sub+'_AP_gib_mppca_b0s.nii.gz') # single b in AP direction
            pab0 = self.join('tmp', sub, sub+'_PA_gib_mppca_b0s.nii.gz') # single b in PA direction
            b0im = self.join('tmp', sub, sub+'_gib_mppca_b0s.nii.gz') # merged b0s AP + PA

            # Load volumes
            dwi_ap, affine_ap = self.load_nifti(apim)
            dwi_pa, affine_pa = self.load_nifti(paim)

            # Extract b0s
            b0s_ap = dwi_ap[:,:,:,gtab.b0s_mask]
            b0s_pa = dwi_pa[:,:,:,[True, True, True, True, False]]

            # Save volumes of b0s
            self.save_nifti(apb0, b0s_ap, affine_ap)
            self.save_nifti(pab0, b0s_pa, affine_pa)

            # Merge into one AP-PA file
            self.sp.run(f'fslmerge -t {b0im} {apb0} {pab0}', shell=True)

            try:
                # Load sidecar jsons and read TRT
                ds = ['AP', 'PA']
                for d in ds:
                    with open(self.join('tmp', sub, sub+f'_{d}.json')) as f:
                        data = json.load(f)
                        ro = data['TotalReadoutTime']
                        if d == 'AP':
                            ap_ro = ro
                            # TODO log
                        else:
                            pa_ro = ro
                            # TODO log
                        f.close()


                with open(acqpar, "w") as f:
                    # for each vol in AP and for each vol in PA
                    for v in range(0, b0s_ap.shape[3]):
                        f.write(f"0 1 0 {ap_ro}\n")
                    for v in range(0, b0s_pa.shape[3]):
                        f.write(f"0 -1 0 {pa_ro}\n")
                    f.close()
            except:
                self.log_error(f'{sub}', f'topup: Could not create acqparams.txt file')
                print(f'{sub} Could not create acqparams.txt file')
                self.log_subjectEnd(sub, 'topup')
                continue

            # Run topup
            self.sp.run(f'topup --imain={b0im} --datain={acqpar} --config=b02b0.cnf \
            --out={self.join("tmp", sub, f"{sub}_topup_results")} \
            --iout={self.join("tmp", sub, f"{sub}_b0_corrected.nii.gz") -v}', shell=True)

            # Copy results to output folder
            if self.copy:
                # Copy results to derivatives
                files = [f'{sub}_AP_gib_mppca.nii.gz', f'{sub}_PA_gib_mppca.nii.gz', \
                f'{sub}_AP.json', f'{sub}_PA.json', f'{sub}_AP.bval', f'{sub}_AP.bvec']
                self.log_info(f'{sub}', f'topup: copying files to derivatives')
                
                try:
                    # yet again the shutil copy fails me, fallback to the cp method
                    for file in [f for f in self.ls(self.join('tmp', sub)) if f not in files and self.isfile(self.join('tmp', sub, f))]:
                        self.sp.run(f'cp {self.join("tmp", sub, ile)} {self.join(self.dataout, sub, file)}', shell=True)
                        self.log_ok(f'sub', f'topup: copied {file} to {self.dataout}')
                    self.log_ok(f'{sub}', f'topup: all files copied to derivatives')
                except:
                    self.log_error(f'{sub}', f'topup: files not copied to derivatives')
                    print(f'{sub} files not copied to derivatives')
                    self.log_subjectEnd(sub, 'topup')
                    continue
            
            # Clean tmp
            if self.clean:
                self.log_info(f'{sub}', f'topup: cleaning tmp folder')
                try:
                    #self.rmtree(self.join('tmp', sub))
                    self.sp.run(f'rm -rf {self.join("tmp", sub)}', shell=True)
                    self.log_ok(f'{sub}', f'topup: tmp folder cleaned')
                except:
                    self.log_error(f'{sub}', f'topup: tmp folder not cleaned')
                    print(f'{sub} tmp folder not cleaned')
                    self.log_subjectEnd(sub, 'topup')
                    continue

            # Log end
            self.log_subjectEnd(sub, 'topup')

        # Log end of all
        # telegram send info
