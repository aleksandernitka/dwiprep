from main import DwiPreprocessingClab as dwipreproc

'''
p = dwipreproc('cost_mppca', 'all',\
    gibbs_method='mrtrix3', \
    datain='/mnt/nasips/COST_mri/derivatives/dwi/',\
    dataout='/mnt/nasips/COST_mri/derivatives/dwi/',\
    threads=4, clean=True, copy=True)'''

p = dwipreproc('cost_mppca', 's', input='sub-65826', \
    gibbs_method='mrtrix3', \
    datain='/mnt/nasips/COST_mri/derivatives/dwi/',\
    dataout='/mnt/nasips/COST_mri/derivatives/dwi/',\
    threads=4, clean=0, copy=0)

p.mppca()
