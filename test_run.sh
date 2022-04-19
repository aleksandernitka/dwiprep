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

# Get infor about gradients
python mk_gradients.py $1 

# denoise with patch2self
python rm_noise_patch2self.py $1

# Extract b0s
python mk_b0s.py $1

# Merge b0s
fslmerge -t tmp/$1_b0s tmp/$1_AP_b0s tmp/$1_PA_b0s
