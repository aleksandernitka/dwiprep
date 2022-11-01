#!bin/bash

export hmridir=/mnt/clab/COST_mri/derivatives/hMRI/
export subdir=/mnt/clab/COST_mri/rawdata/
export tmpdir=/home/aleksander/dwiprep/tmp/
export outdir=/mnt/clab/COST_mri/derivatives/dwipreproc/
export qaldir=/mnt/clab/COST_mri/derivatives/quality/

#$1 id with sub prefix
echo `date +"%D %T"` $1 'started'

# TODO run for all IDs if dwi and st1w exists
# TODO see if tmp dir exists
# TODO rm all files from tmp

# Packages
#conda list --export --json > tmp/conda_env.json

# Cp files required
echo `date +"%D %T"` $1 'cp files'
#python cp_dwifiles.py $1 ${hmridir} ${subdir} ${tmpdir}

# Get infor about gradients
echo `date +"%D %T"` $1 'gradients info'
#python mk_gradients.py $1 

# denoise with patch2self
echo `date +"%D %T"` $1 'denoise'
#python rm_noise_patch2self.py $1

# Extract b0s
echo `date +"%D %T"` $1 'extract and merge b0s'
#python mk_b0s.py $1

# Merge b0s
#fslmerge -t tmp/$1_AP-PA_b0s tmp/$1_AP_b0s tmp/$1_PA_b0s

# Create mean b0 images
#fslmaths tmp/$1_AP_b0s -Tmean tmp/$1_AP_b0s_mean
#fslmaths tmp/$1_PA_b0s -Tmean tmp/$1_PA_b0s_mean

# Make ACQ Params file
#python mk_acqparams.py $1

# Run topup
echo `date +"%D %T"` $1 'run topup'
#topup --imain=tmp/${1}_AP-PA_b0s --datain=tmp/acqparams.txt --out=tmp/$1_AP-PA_topup -v --fout=tmp/$1_AP-PA_fout --iout=tmp/$1_AP-PA_iout --config=b02b0.cnf

# Apply topup
# NB it is NO LONGER SUGGESTED TO  RUN the below, Jesper is not longer recomending this step as the same can be achieved by running eddy with params feed into it https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=FSL;3206abfa.1608
# However I run this to get an undistorted b0 for brainmask
# Furthermore, it will fail unless you add -m jac
echo `date +"%D %T"` $1 'apply topup'
#applytopup -i tmp/$1_AP_denoised.nii.gz -x 1 -a tmp/acqparams.txt -t tmp/$1_AP-PA_topup -o tmp/$1_AP_topup-applied -v -m jac

# Control plots for topup
# TODO fix the below plotting fn
python plt_topup.py $1

# Eddy prep
# TODO since there are no 
# Extract b0s from dwi volume
#python mk_b0s_topupapplied.py $1
# Calc mean b0s from dwi
#fslmaths tmp/$1_AP_b0s_topup-applied -Tmean tmp/$1_AP_b0s_topup-applied_mean
# Get brain mask with BET
#bet tmp/$1_AP_b0s_topup-applied_mean tmp/$1_AP_b0s_topup-applied_bet -m
# plot brain mask
#python plt_brainmask.py $1
# mk and plot alternative mask with otsu
#python mk_otsubrainmask.py $1
# Eddy requires an index file - make it
#python mk_indexeddy.py $1

# Eddy
# run eddy with outlier replacement --repol, slice to volume correction
#eddy_openmp --imain=tmp/$1_AP_denoised --mask=tmp/$1_AP_b0s_topup-applied_otsu_mask.nii.gz --acqp=tmp/acqparams.txt --index=tmp/eddyindex.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --topup=tmp/$1_AP-PA_topup --repol --niter=8 --out=tmp/$1_DWI --verbose --json=tmp/$1_AP.json --cnr_maps

echo `date +"%D %T"` $1 'eddy QC'
eddy_quad tmp/$1_DWI -idx tmp/eddyindex.txt -par tmp/acqparams.txt -m tmp/$1_AP_b0s_topup-applied_otsu_mask.nii.gz -b tmp/$1_AP.bval -v -o tmp/eddyqc

#TODO run eddy-squeeze

echo `date +"%D %T"` $1 'done'
