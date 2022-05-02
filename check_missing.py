import argparse
from os import listdir as ls
from os.path import join

args = argparse.ArgumentParser()
args.add_argument("-o", "--output", help="output file", default=False, required=False, action="store_true")
args.add_argument("-rd", "--rawdir", help="raw data directory", default='/mnt/nasips/COST_mri/rawdata/', type=str, required=False)
args.add_argument("-dp", "--preprcdir", help="preprocessed data directory", default='/mnt/nasips/COST_mri/derivatives/dwi/preproc/', type=str, required=False)
arguments = args.parse_args()

raw = set([f for f in ls(arguments.rawdir) if f.startswith('sub-')])
prp = set([f for f in ls(arguments.preprcdir) if f.startswith('sub-')])

mis = list(raw - prp)

print(f'{len(raw)} subjects in raw data')
print(f'{len(mis)} subjects missing preprocessing:')

for m in mis:
    print(m)

if arguments.output:
    with open('dwi_preproc_missing.txt', 'w') as f:
        for m in mis:
            f.write(m + '\n')

