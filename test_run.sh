#!bin/bash

export hmridir=/mnt/clab/COST_mri/derivatives/hMRI/
export subdir=/mnt/clab/COST_mri/rawdata/
export tmpdir=/home/aleksander/dwiprep/tmp/

#$1 id with sub prefix

echo `date +"%D %T"` $1 'started'

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
#fslmerge -t tmp/$1_b0s tmp/$1_AP_b0s tmp/$1_PA_b0s

# Create mean b0 images
fslmaths tmp/$1_b0s_AP -Tmean tmp/$1_AP_b0s_mean
fslmaths tmp/$1_b0s_PA -Tmean tmp/$1_PA_b0s_mean

# Make ACQ Params file
#python mk_acqparams.py $1

# Run topup
echo `date +"%D %T"` $1 'run topup'
#topup --imain=tmp/${1}_b0s --datain=tmp/acqparams.txt --out=tmp/topup -v --fout=tmp/fout --iout=tmp/iout --config=b02b0.cnf

# Apply topup
echo `date +"%D %T"` $1 'apply topup'
applytopup -i tmp/$1_AP_denoised,tmp/$1_PA_denoised -x 1,2 -a tmp/acqparams.txt -t tmp/topup -o tmp/$1_dwi_tp -v
# Control plots for topup
python plt_topup.py $1

# Eddy prep
# Extract b0s from dwi volume
python mk_b0s_dwi.py $1
# Calc mean b0s from dwi
fslmaths tmp/$1_dwi_b0s -Tmean tmp/$1_dwi_b0s_mean
# Get brain mask with BET
bet tmp/$1_dwi_b0_mean tmp/$1_dwi_b0_brain -m
# plot brain mask
python plt_brainmask.py $1
# mk and plot alternative mask with otsu
python mk_otsubrainmask.py $1
# Eddy requires an index file - make it
python mk_indexeddy.py $1

# Eddy
# run eddy with outlier replacement --repol, slice to volume correction
eddy_openmp --imain=tmp/$1_AP --mask=tmp/$1_dwi_b0_brain_mask_otsu.nii.gz --acqp=tmp/acqparams.txt --index=tmp/eddyindex.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --topup=tmp/res_topup --repol --niter=8 --out=tmp/$1_dwi_tp_eddy --verbose --json=tmp/$1_AP.json --cnr_maps

echo `date +"%D %T"` $1 'eddy QC'
eddy_quad tmp/$1_dwi_tp_eddy -idx tmp/eddyindex.txt -par tmp/acqparams.txt -m tmp/$1_dwi_b0_brain_mask_otsu.nii.gz -b tmp/$1_AP.bval -v -o tmp/eddyqc
echo `date +"%D %T"` $1 'done'
