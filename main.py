class DwiPreprocessingClab():

    # Main analysis class for the MRI processing pipeline
    # Standarises some of the processing steps
    # Developed by Aleksander W. Nitka
    # Relies on the following software:
    # - FSL 6.0.5
    # - DIPY 1.5.0
    # - Fury 0.9.0
    # - Scikit-Learn 
    # - Scikit-Image 
    # - Nilearn 

    def __init__(self, task, mode, input=None, datain=None, dataout=None, \
        qadir=None, threads=-1, telegram=True, verbose=False, clean=True, copy=True, log=True):
        
        # Imports
        from os.path import join, exists, dirname, split, basename, isfile, isdir
        from os import mkdir, makedirs, remove
        from os import listdir as ls
        from dipy.io.image import load_nifti
        import subprocess as sp
        from datetime import datetime as dt

        self.task = task # name of the task performed, used for logging. Can be anything but keep it brief
        self.mode = mode # mode of the pipeline to be run, either single subject, list of subjects or all subjects in a directory
        self.input = input # input file or subject id to be processed
        self.datain = datain # input directory
        self.dataout = dataout # output directory
        self.qadir = qadir # quality assurance directory
        self.threads = threads # number of threads to be used, when possible to set
        self.telegram = telegram # whether to send telegram notifications
        self.verbose = verbose # whether to print verbose messages
        self.clean = clean # whether to clean up the tmp folder after processing
        self.copy = copy # whether to copy the data from tmp to the dataout folder
        self.log = log # whether to log the processing

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
        self.sp = sp
        self.load_nifti = load_nifti
        self.dt = dt

        # Start logging
        self.log_start(self.task)

        # Performs all neccessary checks before starting the processing
        # This should be step 1 in the main script, ALWAYS

        # Check if we are using the correct singularity image
        s, m = self.check_container()
        if not s:
            self.log_error('INIT', m)
            exit(m)
        else:
            print(m)
            self.log_info('INIT', m)
        
        # Check if the input is correct
        s, m = self.check_inputs()
        if not s:
            self.log_error('INIT', m)
            exit(m)
        else:
            print(m)
            self.log_info('INIT', m)
        
        # Check the tmp dir
        s, m = self.check_tmp_dir()
        if not s:
            self.log_error('INIT', m)
            exit(m)
        else:
            print(m)
            self.log_info('INIT', m)

        # Check telegram - no return value
        self.check_telegram()
        
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
            self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')
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
        if self.input == None:
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
                if not self.isdir(self.input):
                    self.log_error('INIT', f'Exit Error. Input directory {self.input} not found.')
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
                print('Subject {sub} directory found in {self.datain}')
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

    def check_tmp_subdir(self, sub):
        # Check if subject directory exists in tmp
        # Create it if it does not exist
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
            # TODO - if found sub dir in tmp, should we delete it?
            return [True, f'Subject {sub} directory found in tmp']

    def check_list_from_file(self):
        # TODO - what this method should do, should it load the data to a list of subs?

        # Should only be run if mode is list or l
        # Return 1 is all is good, if fails return:
        # Check if input exists, fail = 2
        # Check if list is provided from a file, fail = 3
        # Check if the input is a list of subjects, fail = 4
        # If it is a list, check if the subjects are in the datain directory, fail = 5
        # If it is a list, check if the subjects are in the dataout directory
        
        if not self.exists(self.input):
            print(f'Input file not found: {self.input}')
            self.log_error('INIT', f'Input file not found: {self.input}')
            return [False, f'Input file not found: {self.input}']
        else:
            self.log_ok('INIT', f'Input file found: {self.input}')

        if not self.isfile(self.input):
            self.log_error('INIT', f'Input is not a file: {self.input}')
            print(f'Input is not a file: {self.input}')
            return [False, f'Input is not a file: {self.input}']
        else:
            self.log_ok('INIT', f'Input is a file: {self.input}')

        if self.input.endswith('.txt') or self.input.endswith('.csv') or self.input.endswith('.tsv'):
            self.log_ok('INIT', f'Input is a txt-readable file: {self.input}')
            if self.verbose:
                print('Input is a text-readable file')
            
            with open(self.input, 'r') as f:
                subids = f.readlines()
                subids = [subid.strip() for subid in subids]
                print(f'List of subjects: {subids}')
                for subid in subids:
                    subid = self.check_subid(subid)
            self.log_ok('INIT', f'List of {len(subids)} subjects loaded: {subids}')  
            # Now all data has been checked in datain directory. 
        else:
            self.log_error('INIT', f'Input is not a txt-readable file: {self.input}')
            print('Input is not a text-readable file')
            return 4
        
        # If we get here, all is good
        return 1
    
    def check_sub(self, sub):
        # TODO
        # Execute all checks for a subject
        # before running anything for that subject

        # Check if subject directory exists in indir
        # Check if subject directory exists in outdir
        # Check if subject directory exists in tmp/sub

        pass

    def check_list(self):
        # TODO
        # Execute all checks for a list of subjects
        # before running anything for that subject
        pass

    ########################################
    # Helping methods ######################
    ########################################

    def cp_rawdata(self, sub):
        # Copy raw data to tmp folder
        # Returns True or False depending on success and message for logging

        import shutil

        # get all dwi files for pp
        bfs = [f for f in ls(join(self.datain, sub, 'dwi')) if '.DS_' not in f]

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

    def cp_derdata(self, sub, files):
        # TODO
        # Copy derived data to tmp folder
        # Specify file to copy, without the 'sub-00000_' prefix
        pass
    
    ########################################
    # QA methods ###########################
    ########################################
    # Set of QA Methods to check if the data is good enough.
    # Should begin with check_qa method that will set the stage for the rest of the methods
    # Should return True or False depending on the success of the QA

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

    def make_sub_qa_html(self, sub):
        # TODO
        # Make html page for a subject
        # This sets up the html page and should be run before the qa for a single subject
        # as it sets up the html page that will then be read by the qa methods
        # Use self.qadir
        pass

    def make_dwi_qa_html(self):
        # TODO
        # Make html page for dwi data that links to all subs
        # Use self.qadir
        pass

    def run_qa_gibbs(self, sub):
        # TODO
        # Run QA for gibbs ringing
        # Use self.qadir
        pass

    ########################################
    # Plotting methods #####################
    ########################################

    def gif_dwi_4d(self, image, gif, title, slice=55, fdur=500):

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
            images = [Image.open(self.join(tmpDir, i)) for i in ls(self.join(tmpDir)) if i.endswith('.png') and i.startswith('tmp_img')]
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

    def plt_compare_4d(self, file1, file2, sub=None, vols=[0], slice=[50,50,50], \
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
            ax.flat[7].imshow(img1[slice[2],:,:,v].T, cmap=cmap, origin='lower')

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
            fig.savefig(args.out + f'_{v}.png', dpi=300)
            plt.close(fig)

            self.log_ok(f'{sub}', f'plt_compare_4d: Made plots for {file1} and {file2}')
            return [True, f'Comparison plots created for {sub}']
        
    
        # Run GIBS QA
        # Returns True or False depending on success and message for logging

        # First check whether we have QA directory set and whether to run it at all:
        # at at begging or with check_qa method
        if not self.qadir or not self.runqa:
            return [False, f'{sub} QA not run: QA directory not set or QA not set to run']

        # if sub dir in does not exist, then create it - if exists, delete it and create it again
        # if cannot create or delete, then return stop QA and return False
        # also set self.qadir to False and self.runqa to False    
        self.qa_plots_gibs = self.join(self.qadir, 'dwi', 'gibbs', sub)
        if self.exists(self.qa_plots_gibs):
            try:
                self.rmtree(self.qa_plots_gibs)
                self.makedirs(self.qa_plots_gibs)
            except:
                print(f'{sub}  Could not delete or create {self.qa_plots_gibs} directory. QA will not be run.')
                self.qadir = False
                self.runqa = False
                return [False, f'{sub} QA not run: could not delete or create qa_plots_gibs directory: {self.qa_plots_gibs}']
        else:
            try:
                self.makedirs(self.qa_plots_gibs)
                if self.verbose:
                    print(f'{sub} Created QA {self.qa_plots_gibs} directory.')
            except:
                print(f'{sub} Could not create {self.qa_plots_gibs} directory. QA will not be run.')
                self.qadir = False
                self.runqa = False
                return [False, f'QA not run: could not create qa_plots_gibs directory: {self.qa_plots_gibs}']
        
        # QA direcectory is set and exists, so we can run QA

        # check if we have all the files we need
        ap_raw = self.exists(self.join('tmp', sub, f'{sub}_AP.nii'))
        pa_raw = self.exists(self.join('tmp', sub, f'{sub}_PA.nii'))
        ap_gib = self.exists(self.join('tmp', sub, f'{sub}_AP_gibbs.nii.gz'))
        pa_gib = self.exists(self.join('tmp', sub, f'{sub}_PA_gibbs.nii.gz'))

        ims = [ap_raw, pa_raw, ap_gib, pa_gib]

        for n, i in enumerate(ims):
            if not i:
                print(f'{sub} QA Could not find {self.join("tmp", sub, f"{sub}_AP.nii")} cannot plot it.')
            else:
                if self.verbose:
                    print(f'{sub} QA found {self.join("tmp", sub, f"{sub}_AP.nii")}.')

        if not all(ims):
            return [False, f'{sub} QA not run: could not find all the files needed for QA']

        # if we have all the files, then run QA
        # make gif for AP RAW and AP GIBBS

        # Compare volumes for AP RAW and AP GIBBS

        # Compare volumes for PA RAW and PA GIBBS

        # Add to website

        # end of QA GIBBS
        
        return True

    ########################################
    # DWI Preprocessing ####################
    ########################################

    def dipygibbs(self, sub):
        # Run Gibbs ringing correction, for each subject

        # Perform subject checks
        
        self.log_subjectStart(sub, 'dipygibbs')

        if self.verbose:
            print(f'Performing subject checks for {sub}')
        chstat, chmsg = self.perform_subject_checks(sub)
        self.log_info(f'{sub}', f'Performing subject checks for {sub}: {chmsg}')
        if not chstat:
            print(chmsg)
            self.log_subjectEnd(sub, 'dipygibbs')
            return [0, f'Subject {sub} checks failed, subject not processed']
        else:
            if self.verbose:
                print(chmsg)

        # copy raw data to tmp folder
        cpstat, cpmsg = self.cp_rawdata(sub) # will return status code

        # if copied ok, 1 returned, then run gibbs
        if cpstat:
            if self.verbose:
                # TODO - log
                print(cpmsg)
                print(f'Running gibbs ringing correction for {sub}')
            self.log_info(f'{sub}', f'Running gibbs ringing correction for AP {sub}')
            self.sp.run(f'dipy_gibbs_ringing {self.join("tmp", sub, sub + "_AP.nii")} {self.join("tmp", sub, sub + "_AP_gib.nii")}', shell=True)
            self.log_info(f'{sub}', f'Running gibbs ringing correction for PA {sub}')
            self.sp.run(f'dipy_gibbs_ringing {self.join("tmp", sub, sub + "_PA.nii")} {self.join("tmp", sub, sub + "_PA_gib.nii")}', shell=True)

            # TODO QA
        else:
            # Copy was not successful, return error code
            self.log_error(f'{sub}', f'Could not copy raw data for {sub}')
            self.log_subjectEnd(sub, 'dipygibbs')
            return [0, f'Copy of raw data for {sub} was not successful, subject not processed']

        # TODO
        # copy output to dataout folder

        self.log_ok(f'{sub}', f'Gibbs ringing correction for {sub} completed successfully')
        self.log_subjectEnd(sub, 'dipygibbs')
        return [1, f'Gibbs ringing correction for {sub} was successful']

    def dipyp2s(self, sub):
        # TODO
        # Run patch2self
        pass

    def fsleddy(self, sub):
        # TODO
        pass

    def fsltopup(self, sub):
        # TODO
        pass

    ########################################
    # TopLevel Functions ###################
    ########################################
    # These are the functions that are called from the main script
    # so user can evoke those without worrying about the details
    # Note that, for example dipygibbs is called from the main script
    # but it is not a top level function, because it is called from
    # the gibbs function, which is a top level function -- function
    # gibbs will take care of all the checks and logging, and then  
    # call dipygibbs to do the actual work

    def gibbs(self):
        
        # Check if QA required
        [s, m] = self.check_qa(dwi=True)
        if not s:
            # we will not run QA, but still can run the processing
            print(m)
            self.log_warning('INIT', m)
            no_qa_continue = input('Do you want to continue without QA? (y/n): ')
            if no_qa_continue == 'y':
                self.log_warning('INIT', 'User chose to continue without QA')
                print('Continuing without QA')
            if no_qa_continue == 'n':
                self.log_warning('INIT', 'User chose to exit without QA')
                print('Exiting')
                exit(1)
            else:
                self.log_warning('INIT', 'User did not choose y or n, exiting')
                print('Invalid input, exiting')
                exit(1)
        else:
            self.log_ok('INIT', m)
            print(m)
        
        # Check if we have subjects to process
        print(f'{len(self.subs)} subjects to process')
        self.log_info('INIT', f'{len(self.subs)} subjects to process for gibbs ringing correction, taks name: {self.task}')

        # dump the list of subjects to process to a file
        self.log_subdump(self.subs)

        # Loop over subjects
        for i, sub in enumerate(self.subs):
            print(f'Processing subject {sub} ({i+1}/{len(self.subs)} for gibbs ringing correction')
            self.dipygibbs(sub)
        
        if self.telegram:
            self.log_ok('ALL', f'Gibbs ringing correction completed successfully for {len(self.subs)} subjects')
            self.tg('Gibbs ringing correction completed for all subjects')

