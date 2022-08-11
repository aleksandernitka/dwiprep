# dwiprep
## Info
A set of preprocessing tools used in DWI preprocessing. The scripts with `run_` prefix are used to run separate stages of preprocessing. In essence, these are python wrappers around FSL's command line tools, containers and DIPY functions.
The key tools used are:

* DIPY 1.5.0 patch2self denoising
* FSL TopUp
* FSL Eddy
* SynthStrip

Furthermore, a few QC tools, mainly control plots, were also implemented using matplotlib and nilearn. And so (will) be a method of aggregating key QC metrics onto a html page.

Please note, that the process was split into separate stages to facilitate an extensive dataset. For a smaller data these steps can be run as one script.

## Stages
The process of preprocessing was split into separate stages. The following stages are implemented and should be run in sequence:
1. `run_denoise.py`: Denoising of DWI data using DIPY's `path2self`. 
2. `run_topup.py`: Calculates topup distortion correction using FSL. 
3. `run_eddy.py`: Applies topup and performs eddy current correction, also creates QC report for the two.
4. `run_preproc_summary.py`: Creates a summary of the preprocessing steps, puts all control plots together into a easy-to-view website.

## TODO
1. Adopt argparse in all run-scripts
2. Adopt containers in all run-scripts
3. Complete the html qc building script
4. Remove `run_pre_topup.py`