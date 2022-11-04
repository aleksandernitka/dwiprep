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
        import time as t

        self.sub = sub
        self.datadir = datadir

        # mkdir in data
        mkdir(join('data', sub))

        experiment = ['oneb0_raw', 'allb0_raw', 'oneb0_gibbs', 'allb0_gibbs', 'oneb0_mppca', 'allb0_mppca']
        for e in experiment:
            mkdir(join('data', sub, e))

        # Load the data
        files = [f'{self.sub}_AP.nii', f'{self.sub}_PA.nii',\
            f'{self.sub}_AP_gib.nii.gz', f'{self.sub}_PA_gib.nii.gz',\
            f'{self.sub}_AP_gib_mppca.nii.gz', f'{self.sub}_PA_gib_mppca.nii.gz', \
            f'{self.sub}_AP.json', f'{self.sub}_PA.json', f'{self.sub}_AP.bval', f'{self.sub}_AP.bvec']    
            
        for file in files:
            try:
                copyfile(join(datadir, sub, file), join('data', sub, file))
                print(f'topup: Copied {file} to data folder')
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
        # Input files
        ap_raw = join("data", self.sub, self.sub+"_AP.nii")
        pa_raw = join("data", self.sub, self.sub+"_PA.nii")
        ap_gib = join("data", self.sub, self.sub+"_AP_gib.nii.gz")
        pa_gib = join("data", self.sub, self.sub+"_PA_gib.nii.gz")
        ap_mppca = join("data", self.sub, self.sub+"_AP_gib_mppca.nii.gz")
        pa_mppca = join("data", self.sub, self.sub+"_PA_gib_mppca.nii.gz")

        # Output files, extracted b0s for oneb0 condition
        ap_raw_oneb0 = join("data", self.sub, 'oneb0_raw', self.sub+"_AP_raw_oneb0.nii.gz")
        pa_raw_oneb0 = join("data", self.sub, 'oneb0_raw', self.sub+"_PA_raw_oneb0.nii.gz")
        ap_gib_oneb0 = join("data", self.sub, 'oneb0_gibbs', self.sub+"_AP_gibbs_oneb0.nii.gz")
        pa_gib_oneb0 = join("data", self.sub, 'oneb0_gibbs', self.sub+"_PA_gibbs_oneb0.nii.gz")
        ap_mppca_oneb0 = join("data", self.sub, 'oneb0_mppca', self.sub+"_AP_mppca_oneb0.nii.gz")
        pa_mppca_oneb0 = join("data", self.sub, 'oneb0_mppca', self.sub+"_PA_mppca_oneb0.nii.gz")

        # Output files, extracted b0s for allb0 condition
        ap_raw_allb0 = join("data", self.sub, 'allb0_raw', self.sub+"_AP_raw_allb0.nii.gz")
        pa_raw_allb0 = join("data", self.sub, 'allb0_raw', self.sub+"_PA_raw_allb0.nii.gz")
        ap_gib_allb0 = join("data", self.sub, 'allb0_gibbs', self.sub+"_AP_gibbs_allb0.nii.gz")
        pa_gib_allb0 = join("data", self.sub, 'allb0_gibbs', self.sub+"_PA_gibbbs_allb0.nii.gz")
        ap_mppca_allb0 = join("data", self.sub, 'allb0_mppca', self.sub+"_AP_mppca_allb0.nii.gz")
        pa_mppca_allb0 = join("data", self.sub, 'allb0_mppca', self.sub+"_PA_mppca_allb0.nii.gz")

        # Merged AP-PA for topup
        appa_raw_oneb0 = join("data", self.sub, 'oneb0_raw', self.sub+"_AP-PA_raw_oneb0.nii.gz")
        appa_gib_oneb0 = join("data", self.sub, 'oneb0_gibbs', self.sub+"_AP-PA_gibbs_oneb0.nii.gz")
        appa_mppca_oneb0 = join("data", self.sub, 'oneb0_mppca', self.sub+"_AP-PA_mppca_oneb0.nii.gz")
        appa_raw_allb0 = join("data", self.sub, 'allb0_raw', self.sub+"_AP-PA_raw_allb0.nii.gz")
        appa_gib_allb0 = join("data", self.sub, 'allb0_gibbs', self.sub+"_AP-PA_gibbs_allb0.nii.gz")
        appa_mppca_allb0 = join("data", self.sub, 'allb0_mppca', self.sub+"_AP-PA_mppca_allb0.nii.gz")

        # Extract the b0s SINGLE b0 in each direction
        sp.run(f'fslroi {ap_raw} {ap_raw_oneb0} 0 1', shell=True)
        sp.run(f'fslroi {pa_raw} {pa_raw_oneb0} 0 1', shell=True)
        sp.run(f'fslroi {ap_gib} {ap_gib_oneb0} 0 1', shell=True)
        sp.run(f'fslroi {pa_gib} {pa_gib_oneb0} 0 1', shell=True)
        sp.run(f'fslroi {ap_mppca} {ap_mppca_oneb0} 0 1', shell=True)
        sp.run(f'fslroi {pa_mppca} {pa_mppca_oneb0} 0 1', shell=True)

        # Merge the b0s, SINGLE b0 in each direction
        sp.run(f'fslmerge -t {appa_raw_oneb0} {ap_raw_oneb0} {pa_raw_oneb0}', shell=True)
        sp.run(f'fslmerge -t {appa_gib_oneb0} {ap_gib_oneb0} {pa_gib_oneb0}', shell=True)
        sp.run(f'fslmerge -t {appa_mppca_oneb0} {ap_mppca_oneb0} {pa_mppca_oneb0}', shell=True)

        
        # Extract all b0s ALL b0s in each direction

        # Create b0 mask
        gtab = gradient_table(f'data/{sub}/{sub}_AP.bval', f'data/{sub}/{sub}_AP.bvec')

        all_vols = [[ap_raw, pa_raw], [ap_gib, pa_gib], [ap_mppca, pa_mppca]]
        all_file = [[ap_raw_allb0, pa_raw_allb0], [ap_gib_allb0, pa_gib_allb0], [ap_mppca_allb0, pa_mppca_allb0]]
        all_merg = [appa_raw_allb0, appa_gib_allb0, appa_mppca_allb0]
        
        for i, v in enumerate(all_vols):
        
            try:
                # Load volumes
                dwi_ap, affine_ap = load_nifti(all_vols[i][0])
                dwi_pa, affine_pa = load_nifti(all_vols[i][1])

                # Extract b0s
                b0s_ap = dwi_ap[:,:,:,gtab.b0s_mask]
                b0s_pa = dwi_pa[:,:,:,[True, True, True, True, False]]

                # Save volumes of b0s
                save_nifti(all_file[i][0], b0s_ap, affine_ap)
                save_nifti(all_file[i][1], b0s_pa, affine_pa)

                # Merge into one AP-PA file
                sp.run(f'fslmerge -t {all_merg[i]} {all_file[i][0]} {all_file[i][1]}', shell=True)
                print(f'Merged {all_file[i][0]} and {all_file[i][1]} into {all_merg[i]}')
            except:
                print(f'{self.sub} Could not extract b0s')
                continue 
        
        # Create topup config file
        # Load sidecar jsons and read TRT
        ds = ['AP', 'PA']
        for d in ds:
            with open(join('data', self.sub, self.sub+f'_{d}.json')) as f:
                data = json.load(f)
                ro = data['TotalReadoutTime']
                if d == 'AP':
                    ap_ro = ro
                else:
                    pa_ro = ro
                f.close()


        # Create config file oneb0
        with open(join('data', self.sub, self.sub+'_acqparam_oneb0.txt'), 'w') as f:
            f.write(f'0 -1 0 {ap_ro}\n0 1 0 {pa_ro}')
            f.close()
        
        # Create config file allb0s
        with open(join("data", self.sub, self.sub+'_acqparam_allb0.txt'), "w") as f:
            # for each vol in AP and for each vol in PA
            for v in range(0, b0s_ap.shape[3]):
                f.write(f"0 -1 0 {ap_ro}\n")
            for v in range(0, b0s_pa.shape[3]):
                f.write(f"0 1 0 {pa_ro}\n")
            f.close()

        with open (join("data", self.sub, self.sub+'_timings.txt'), "w") as f:
            f.write('sub\texp\ttime')

        for e in experiment:
            print(f'Running experiment {e} for {self.sub}')
            
            set_b0s = e.split('_')[0]
            set_stp = e.split('_')[1]

            # Setup topup
            acqparam = join('data', self.sub, self.sub+f'_acqparam_{set_b0s}.txt')
            
            # Set imain
            mainimg = join('data', self.sub, e, self.sub+f'_AP-PA_{set_stp}_{set_b0s}.nii.gz')
            
            print(f"Running topup for {self.sub} with {self.sub+f'_AP-PA_{set_stp}_{set_b0s}.nii.gz'} for {e}")

            # timer start
            tic = t.perf_counter()

            sp.run(f'topup --imain={mainimg} --datain={acqparam} --config=b02b0.cnf \
            --out={join("data", sub, e, f"{sub}_{e}_tp_res_")} \
            --iout={join("data", sub, e, f"{sub}_{e}_b0_cor.nii.gz")}', shell=True)

            # timer stop
            toc = t.perf_counter()
            
            with open (join("data", self.sub, self.sub+'_timings.txt'), "a") as f:
                f.write(f'{self.sub}\t{e}\t{toc-tic}\n')

            print(f"Finished topup {e} for {self.sub} in {toc - tic:0.4f} seconds")

        print(f"{self.sub} finished all experiments")
        f.close()

exp = topupExperiment(sub = args.subject, datadir=args.data_dir)