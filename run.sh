#!bin/bash

export hmridir=/mnt/clab/COST_mri/derivatives/hMRI/
export subdir=/mnt/clab/COST_mri/rawdata/
export tmpdir=/home/aleksander/dwiprep/tmp/

#$1 id with sub prefix

echo `date +"%D %T"` $1 'preprocessing started'

# Packages
conda list --export --json > tmp/conda_env.json

# Cp files required
python cp_dwifiles.py $1 ${hmridir} ${subdir} ${tmpdir}
'''
# Get infor about gradients
# TODO dumps core for some reason?
python mk_gradients.py $1 

# mk acqparams file for topup and eddys
python mk_acqparams.py 

# denoise with patch2self
echo `date +"%D %T"` $1 'denoising started'
python rm_noise_patch2self.py $1

echo `date +"%D %T"` $1 'done'

# Extract b0s
fslroi tmp/$1_AP tmp/$1_AP_b0 0 1
fslroi tmp/$1_PA tmp/$1_PA_b0 0 1

# Merge b0s
fslmerge -t tmp/$1_b0 tmp/$1_AP_b0 tmp/$1_PA_b0

# Run topup
echo `date +"%D %T"` $1 'running topup'
# for some reason --config=b02b0.cnf is causig problems, try to run on KPC
topup --imain=tmp/${1}_b0 --datain=tmp/acqparams.txt --out=tmp/res_topup --fout=tmp/fout --iout=tmp/iout --config=b02b0.cnf

echo `date +"%D %T"` $1 'applying topup'
applytopup --imain=tmp/$1_AP --inindex=1 --datain=tmp/acqparams.txt --topup=tmp/res_topup --method=jac --out=tmp/$1_dwi 
 
echo `date +"%D %T"` $1 'control plots post topup'
python plt_topup.py $1

echo `date +"%D %T"` $1 'eddy'
# first we need a brain mask
fslroi tmp/$1_dwi tmp/$1_dwi_b0 0 1
fslmaths tmp/$1_dwi_b0 -Tmean tmp/$1_dwi_b0
bet tmp/$1_dwi_b0 tmp/$1_dwi_b0_brain -m
# plot brain mask
python plt_brainmask.py $1
# mk and plot alternative amsk with otsu
python mk_otsubrainmask.py $1
# Eddy requires an index file - make it
python mk_indexeddy.py $1
# run eddy with outlier replacement --repol, slice to volume correction
eddy_openmp --imain=tmp/$1_AP.nii.gz --mask=tmp/$1_dwi_b0_brain_mask_otsu.nii.gz --acqp=tmp/acqparams.txt --index=tmp/eddyindex.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --topup=tmp/res_topup --repol --niter=8 --out=tmp/$1_dwi_cor --verbose --json=tmp/$1_AP.json --cnr_maps
#eddy --imain=tmp/$1_AP.nii.gz --mask=tmp/$1_dwi_b0_brain_mask_otsu.nii.gz --index=tmp/eddyindex.txt --acqp=tmp/acqparams.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --fwhm=0 --topup=tmp/res_topup --flm=quadratic --out=tmp/AP_eddy_unwarped 

echo `date +"%D %T"` $1 'eddy QC'
eddy_quad tmp/$1_dwi_cor -idx tmp/eddyindex.txt -par tmp/acqparams.txt -m tmp/$1_dwi_b0_brain_mask_otsu.nii.gz -b tmp/$1_AP.bval -v -o tmp/eddyqc
echo `date +"%D %T"` $1 'done'
'''

