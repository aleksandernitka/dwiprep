# DWI Preprocessing for COST (Kraków implementation)

## Singularity
Singularity is an open source container management software. It is used to run the pipeline in a reproducible environment. By using container one does not have to worry about the software being installed in the OS, all required software is already included in the container. 

### Downloading and installing Singularity 
To install the software please follow the guide on the [Singularity website](https://sylabs.io/guides/3.5/user-guide/quick_start.html#quick-installation-steps). If you are using the Kraken the Singularity is already installed and can be accessed from the terminal. 

### Building the container image
The container is built from the definition file in the repository (`singularity/dwi_preproc.def`). If you wish you can inspect the file with your favorite text editor. The definition file was constructed with neurodocker using the following command:
```bash
neurodocker generate singularity -p apt -b debian:bullseye-slim --fsl version=6.0.5 --mrtrix3 version=3.0.2 --miniconda version=py39_4.12.0 conda_install="jupyter jupyterlab dipy=1.5.0 fury=0.8.0 scikit-learn=1.1.2 scikit-image=0.19.3 pillow nilearn=0.9.0" --run "touch /opt/dwiprep.txt" --install git vim nano htop tree wget > singularity/dwi_preproc.def
```
Please be mindfull that the process may take a pretty while, due to the time it takes to install FSL. 

To build the image from the definition file run the following command in the repository directory:
```bash
sudo singularity build singularity/dwi_preproc.sif singularity/dwi_preproc.def
```
This has to be run only once, it will create a file `dwi_preproc.sif` in the `singularity` directory which is the container image with all software installed inside the container. If you do not have `sudo` access you can build the image with the `--fakeroot` option or request it from the system administrator.

### Running the container
To run the container you will need to mount the `mnt` directory to the container. The `mnt` directory is the directory where the data is accessed from. To start the shell in the container will be run with the following command:
```
singularity shell --bind mnt:/mnt singularity/dwi_preproc.sif
```
If all went well you should see the following prompt:
```
Singularity> 
```
This is the shell inside the container. You can run any command you would run in the terminal, but all the software is already installed in the container. To exit the shell type `exit` or press `Ctrl+D`.

## Preprocessing
The preprocessing is done with methods implemented in `dwiprep/main.py`. To run the processing, one must import the preprocessing class from the `main.py` such as:
```python
from dwiprep.main import DwiPreprocessingClab
```
To initialise the preprocessing determine what kind of preprocessing you want to do. There are three key settings which one should supply; mode of work, input, and output dirs. 

```python
my_preproc = DwiPreprocessingClab(task='my_preprocessing', mode='all', datain='mnt/krakow/raw', output_dir='mnt/krakow')
```
alternatively, when wanting to only for a single subject:
```python
my_preproc = DwiPreprocessingClab(task='my_single_subject_preprocessing', mode='sub', input='sub-00001', datain='mnt/krakow/raw', output_dir='mnt/krakow')
```

In both cases this declaration will only store the choices, but will not run the process itself. The instatialisation can take more arguments:

* `task` must specify name of the task, something to id this analysis, 
* `mode` must be set as either `'all'` or `'a'`, `'list'` or `'l'`, or `'subject'` or `'s'`. This determines what data is going to be processed. `'all'` will process all subjects in the `datain` directory, `'list'` will process only subjects specified in the `input` argument, and `'subject'` will process only the subject specified in the `input` argument.
* `input` what is going to be supplied here depends on the mode selected; fo `'all'` this can be skipped, for `'list'` a valid csv list of subject should be mapped and for `'sub'` one should specify the subject name as a string.
* `datain` is the directory where the raw data is stored. The directory should contain the `sub-XXXXX` directories with the raw data (when running the first step of the pipeline) or derivatives (when running the second and later steps of the pipeline).
* `dataout` where the data should be moved to after the processing. The directory should contain the `sub-XXXXX` directories with the processed data.
* `threads` specifies the number of threads to use for the processing. The default is all. Please note that this currently cannot be relied upon, for example the patch2self method will always use all threads available and at this point I do not know how to control this beast. 
* `telegram` specifies whether to send the status of the processing to the telegram bot. The default is `True`, but requires setup of the telegram bot.
* `verbose` when set to true, the processing will spit a bit more information to the terminal. The default is `False`.
* `clean` when set to true, the processing will remove the temporary files after the processing. The default is `True`.
* `copy` when set to true, the processing will copy the data to the `dataout` directory. The default is `True`.
* `log` when set to true, the processing will log the output to the `log` directory. The default is `True`.
* `check_container` when set to true, the processing will check if the container, the one we provide the def file for, has been loaded, if set to `True` the process will stop if a different or no container is used. The default is `True`.
* `n_coils` some processes require this information for accurate estimation, this has been set to `32` but may be experiment or setup dependent. This should be in json sidecards in your data. 

### Preprocessing steps
The below steps have been implemented in the preprocessing class. The steps are run in the order they are listed below, but this is not a strict requirement. Order can be adjusted, with some minute change to the code. This can be expanded in the future to have more interoperability between the steps, it would require a modification to the `cp_rawdata()` method embedded into the `gibbs()` method; all other steps rely on the data from derivatives. For example step 0 could be implemented, it would copy, rename all the rawdata to the derivatives directory, and then the rest of the steps could be run. 

#### Gibbs ringing correction
The first step of the preprocessing is the Gibbs ringing correction. This is done with the `gibbs_ringing_correction` method from DIPY 1.5.0. The method takes no arguments, but requires the preprocessing to be initialised (see above). The method will run the Gibbs ringing correction on all subjects declared in the setup (see above) then move the data to the `dataout` directory. The method will also create a log file in the `log` directory and control plots in the `imgs/gibbs/` directory. To run for all subjects:

```python
my_preproc.gibbs()
```

#### Denoising with Patch2Self
The (usually) second step of the preprocessing is the denoising with Patch2Self. This is done with the `denoise_patch2self` method from DIPY 1.5.0. The method takes no arguments, but requires the preprocessing to be initialised (see above). The method will run the denoising with Patch2Self on all subjects declared in the setup (see above) then move the data to the `dataout` directory. The method will also create a log file in the `log` directory and control plots in the `imgs/denoise/` directory. To run for all subjects:

```python
my_preproc.patch2self()
```

Please note that this will take a considerable amount of time to run, depending on the number of subjects and the number of threads used. 

#### TopUp distortion estimation
The (usually) third step of the preprocessing is the estimation of the distortion with TopUp. This is done with the `topup` method from FSL 6.0.4. The method takes no arguments, but requires the preprocessing to be initialised (see above). The method will run the estimation of the distortion with TopUp on all subjects declared in the setup (see above) then move the data to the `dataout` directory. The method will also create a log file in the `log` directory and control plots in the `imgs/topup/` directory. To run for all subjects:

```python
my_preproc.topup()
```

#### Eddy current correction and bias field correction
The (usually) fourth and final step of the preprocessing is the Eddy current correction and bias field correction. This is done with the `eddy` method from FSL 6.0.4. The method takes no arguments, but requires the preprocessing to be initialised (see above). The method will run the Eddy current correction and bias field correction on all subjects declared in the setup (see above) then move the data to the `dataout` directory. The method will also create a log file in the `log` directory and control plots in the `imgs/eddy/` directory. To run for all subjects:

```python
my_preproc.eddy()
```

## Quality Assurance and Control
At each stage of the process control plots are created to make inspection of the data more convenient. The plots are saved in the `imgs` directory, in the subdirectory corresponding to the step of the processing. The plots are saved in the `png` format and can be viewed on any computer. However, the navigation between subjects and steps may cause trouble, therefore the final function can be used to create html reports with all the plots. 
