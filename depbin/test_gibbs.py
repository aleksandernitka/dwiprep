from dipy.denoise.gibbs import gibbs_removal
from dipy.io.image import load_nifti_data
import matplotlib.pyplot as plt
from os.path import join

sub = 'sub-13333'

api = join('/mnt/nasips/COST_mri/derivatives/dwi/', sub, f'{sub}_AP.nii')

# Load the data
d, a = load_nifti_data(api)
d_unr = gibbs_removal(d, slice_axis=2, num_threads=4)

# Plot the data
fig, ax = plt.subplots(1, 2, figsize=(10, 5))
ax[0].imshow(d[0, :, 0, :].T, cmap='gray', origin='lower')
ax[0].set_title('Original')
ax[1].imshow(d_unr[0, :, 0, :].T, cmap='gray', origin='lower')
ax[1].set_title('Gibbs removed')
plt.savefig(f'{sub}_gibs.png')

