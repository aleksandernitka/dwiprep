#!bin/bash

export hmridir=/mnt/nasips/COST_mri/derivatives/hMRI/
export subdir=/mnt/nasips/COST_mri/rawdata/
export tmpdir=/home/aleksander/dwiprep/tmp/

#$1 id with sub prefix

echo $1 'preprocessing started'

# Cp files required
python cp_dwifiles.py $1 ${hmridir} ${subdir} ${tmpdir}

# mk acqparams file for topup and eddy
python mk_acqparams.py 

# Extract b0s
fslroi tmp/$1_AP tmp/$1_AP_b0 0 1
fslroi tmp/$1_PA tmp/$1_PA_b0 0 1
# 
# Merge b0s
fslmerge -t tmp/$1_b0 tmp/$1_AP_b0 tmp/$1_PA_b0
# 
# Run topup
echo $1 'running topup'
# for some reason --config=b02b0.cnf is causig problems, try to run on KPC
#topup --imain=tmp/${1}_b0 --datain=tmp/acqparams.txt --out=tmp/res_topup --fout=tmp/fout --iout=tmp/iout
# 
 echo $1 'applying topup'
#applytopup --imain=tmp/$1_AP --inindex=1 --datain=tmp/acqparams.txt --topup=tmp/res_topup --method=jac --out=tmp/$1_dwi 
# 
 echo $1 'control plots post topup'
python plt_topup.py $1

echo $1 'eddy'
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
#eddy --imain=tmp/$1_dwi --mask=tmp/$1_dwi_b0_brain_mask_otsu --acqp=tmp/acqparams.txt --index=tmp/eddyindex.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --topup=tmp/res_topup --repol --niter=8 --fwhm=10,8,4,2,0,0,0,0 --out=tmp/$1_dwi_cor --niter=8 --fwhm=10,8,4,2,0,0,0,0 --verbose > tmp/eddylog.txt
eddy --imain=tmp/$1_AP.nii.gz --mask=tmp/$1_dwi_b0_brain_mask_otsu.nii.gz --index=tmp/eddyindex.txt --acqp=tmp/acqparams.txt --bvecs=tmp/$1_AP.bvec --bvals=tmp/$1_AP.bval --fwhm=0 --topup=tmp/res_topup --flm=quadratic --out=AP_eddy_unwarped --data_is_shelled



