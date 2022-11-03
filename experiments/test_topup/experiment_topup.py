import argparse

args = argparse.ArgumentParser()
args.add_argument('subject', help='Subject ID')
args.add_argument('data_dir', help='Data directory')
args = args.parse_args()

class topupExperiment():
    def __init__(self, sub, datadir):

        from dipy.io.image import load_nifti, save_nifti
        from dipy.core.gradients import gradient_table
        from os.path import join
        from os import mkdir
        from shutil import copyfile
        import subprocess as sp
        import json

        self.sub = sub
        self.datadir = datadir

        # mkdir in tmp
        mkdir(join('data', sub))

        # Load the data
        files = [f'{self.sub}_AP.nii', f'{self.sub}_PA.nii',\
            f'{self.sub}_AP_gib.nii.gz', f'{self.sub}_PA_gib.nii.gz',\
            f'{self.sub}_AP_gib_mppca.nii.gz', f'{self.sub}_PA_gib_mppca.nii.gz', \
            f'{self.sub}_AP.json', f'{self.sub}_PA.json', f'{self.sub}_AP.bval', f'{self.sub}_AP.bvec']    
            
        for file in files:
            try:
                copyfile(join(datadir, sub, file), join('tmp', sub, file))
                print(f'topup: Copied {file} to tmp folder')
            except:
                print(f'Could not copy file {file}')
                continue
        
        

        # Condition 1: Extract the b0s from the AP and PA scans
        #   A: just the first image from AP and PA
        #   B: all b0 images from AP and PA
        # Condition 2: Type of image
        #   A: raw
        #   B: gibbs
        #   C: gibbs + mppca <- already done for the AP and PA scans with all b0s used for topup
        # These are coded as:
        # oneb0_raw
        # allb0_raw
        # oneb0_gibbs
        # allb0_gibbs
        # oneb0_mppca
        # allb0_mppca

        # Extract single b0 from all steps
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_AP.nii")} {join("tmp", self.sub, self.sub+"_AP_oneb0.nii.gz")} 0 1', shell=True)
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_PA.nii")} {join("tmp", self.sub, self.sub+"_PA_oneb0.nii.gz")} 0 1', shell=True)
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_AP_gib.nii.gz")} {join("tmp", self.sub, self.sub+"_AP_gib_oneb0.nii.gz")} 0 1', shell=True)
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_PA_gib.nii.gz")} {join("tmp", self.sub, self.sub+"_PA_gib_oneb0.nii.gz")} 0 1', shell=True)
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_AP_gib_mppca.nii.gz")} {join("tmp", self.sub, self.sub+"_AP_gib_mppca_oneb0.nii.gz")} 0 1', shell=True)
        self.sp.run(f'fslroi {join("tmp", self.sub, self.sub+"_PA_gib_mppca.nii.gz")} {join("tmp", self.sub, self.sub+"_PA_gib_mppca_oneb0.nii.gz")} 0 1', shell=True)

        # Extract all b0s from all steps
        # load gradient table
        #try:
        # Create b0 mask
        try:
            gtab = gradient_table(f'tmp/{sub}/{sub}_AP.bval', f'tmp/{sub}/{sub}_AP.bvec')
        except:
            print(f'{sub} Could not create gradient table')
            continue

        # Prepare data for topup
        # Extract b0s
        ap_vols = ['_AP.nii', '_AP_gib.nii.gz'] # for third step, download from the server, as it has already been done
        pa_vols = ['_PA.nii', '_PA_gib.nii.gz']

        for v in range(0, len(ap_vols)):
        
            try:
                # Load volumes
                dwi_ap, affine_ap = load_nifti(join('tmp', self.sub, self.sub+ap_vols[v]))
                dwi_pa, affine_pa = load_nifti(join('tmp', self.sub, self.sub+pa_vols[v]))

                # Extract b0s
                b0s_ap = dwi_ap[:,:,:,gtab.b0s_mask]
                b0s_pa = dwi_pa[:,:,:,[True, True, True, True, False]]

                ap_name = self.sub+ap_vols[v].split('.')[0]+'_allb0.nii.gz'
                pa_name = self.sub+pa_vols[v].split('.')[0]+'_allb0.nii.gz'
                fi_name = self.sub+ap_vols[v].replace('AP', 'APPA').split('.')[0]+'_allb0.nii.gz'

                # Save volumes of b0s
                save_nifti(join("tmp", self.sub, ap_name), b0s_ap, affine_ap)
                save_nifti(join("tmp", self.sub, pa_name), b0s_pa, affine_pa)

                # Merge into one AP-PA file
                self.sp.run(f'fslmerge -t {join("tmp", self.sub, ap_name)} {join("tmp", self.sub, pa_name)} {join("tmp", self.sub, self.sub+fi_name)}', shell=True)
            except:
                print(f'{sub} Could not extract b0s')
                continue 
        
        # Create topup config file
        # Load sidecar jsons and read TRT
        ds = ['AP', 'PA']
        for d in ds:
            with open(join('tmp', sub, sub+f'_{d}.json')) as f:
                data = json.load(f)
                ro = data['TotalReadoutTime']
                if d == 'AP':
                    ap_ro = ro
                else:
                    pa_ro = ro
                f.close()


        # Create config file oneb0
        with open(join('tmp', sub, sub+'_acqparam_oneb0.txt'), 'w') as f:
            f.write(f'0 -1 0 {ap_ro}')
            f.write(f'0 1 0 {pa_ro}')
            f.close()
        
        # Create config file allb0s
        with open(join("tmp", self.sub, self.sub+'_acqparam_allb0.txt'), "w") as f:
            # for each vol in AP and for each vol in PA
            for v in range(0, b0s_ap.shape[3]):
                f.write(f"0 -1 0 {ap_ro}\n")
            for v in range(0, b0s_pa.shape[3]):
                f.write(f"0 1 0 {pa_ro}\n")
            f.close()

    
        experiment = ['oneb0_raw', 'allb0_raw', 'oneb0_gibbs', 'allb0_gibbs', 'oneb0_mppca', 'allb0_mppca']
        
        for e in experiment:
            print(f'Running experiment {e} for {sub}')
            mkdir(join('data', sub, e))
            # Run topup
            if 'oneb0' in e:
                acqparam = join('tmp', sub, sub+'_acqparam_oneb0.txt')
            else:
                acqparam = join('tmp', sub, sub+'_acqparam_allb0.txt')
            
            

            self.sp.run(f'topup --imain={b0im} --datain={acqparam} --config=b02b0.cnf \
            --out={self.join("tmp", sub, f"{sub}_topup_results")} \
            --iout={self.join("tmp", sub, f"{sub}_b0_corrected.nii.gz")} -v', shell=True)