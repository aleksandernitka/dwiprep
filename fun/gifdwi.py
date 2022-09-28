import argparse
import matplotlib.pyplot as plt
from os.path import join, exists, dirname
from os import listdir as ls
from os import remove
from dipy.io.image import load_nifti
from PIL import Image

a = argparse.ArgumentParser(description="Creates GIF from DWI volumes")
a.add_argument('input', help='Input: path to DWI volume (file.nii or nii.gz)')
a.add_argument('output', help='Output: path to output GIF')
a.add_argument('-s', '--slice', help='Slice to use for GIF', default=55, type=int)
a.add_argument('-t', '--title', help='Title for GIF', default='DWI', type=str)
a = a.parse_args()

# Need path to dump tmp images
tmpDir = dirname(a.output)

try:
    img, aff = load_nifti(a.input)
except:
    print(f'Could not load {a.input}')
    exit(1)

if not exists(dirname(a.output)):
    print(f'Could not locate {dirname(a.output)}')
    exit(1)

print('Extracting volumes...')
# Make PNGs
for v in range(img.shape[-1]):
    fig, ax = plt.subplots(1,3, figsize=(15,5), subplot_kw=dict(xticks=[], yticks=[]))
    fig.subplots_adjust(hspace=0.25, wspace=0.25)
    fig.suptitle(f'{a.title}', fontsize=16)
    plt.tight_layout()
    ax.flat[0].imshow(img[:, :, a.slice, v].T, origin='lower', cmap='gray')
    ax.flat[1].imshow(img[:, a.slice, :, v].T, origin='lower', cmap='gray')
    ax.flat[2].imshow(img[a.slice, :, :, v].T, origin='lower', cmap='gray')
    
    fig.savefig(join(tmpDir, f'tmp_img{1000+v}.png'))
    plt.close(fig)

# Make GIF
print('Compiling GIF...')
images = [Image.open(join(tmpDir, i)) for i in ls(join(tmpDir)) if i.endswith('.png') and i.startswith('tmp_img')]
image1 = images[0]
image1.save(join(a.output), format = "GIF", save_all=True, append_images=images[1:], duration=1000, loop=0)

# Clean up
print('Cleaning up...')
for i in ls(join(tmpDir)):
    if i.endswith('.png') and i.startswith('tmp_img'):
        remove(join(tmpDir, i))

