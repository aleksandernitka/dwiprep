#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the test which compares two orders of preprocessing:
1. Gibbs derining then patch2self
2. Patch2self then Gibbs.

This script performs end-to-end test.

Requires:
* Connection to the remote store with the raw DWI data.
* DIPY 1.5.0
"""
import subprocess as sp
import argparse
import numpy as np
from os import mkdir
from os.path import exists

args = argparse.ArgumentParser(description='Runs the test end to end. If required set the location of rawdata files and seed.')
args.add_argument('-d', '--dir', help='Where the rawdata is; it assumes that next level is sub- then the dwi dir inside it.', default='/mnt/nasips/COST_mri/rawdata')
args.add_argument('-s', '--seed', help='Seed is required for the selection of random subs, default is 42, use integers.', default=42, type=int)
args.add_argument('-n', '--n', help='Sample size', default=10, type=int)
args.add_argument('-c','--nocopy', help='Do not copy the data, data already present in data dir', default=False, action='store_true')
args = args.parse_args()

# Select files to test, seed set for reproducability as 42
sp.run(f'python select_sub.py {args.dir} -n {args.n} -s {args.seed} -o', shell=True)

# Copy data to local
## Load test subject ids
try:
    sample = np.loadtxt('random_sample.txt', dtype=int)
except:
    print('Cannot load the random_sample.txt')
    exit(1)

## Download each set
if not args.nocopy:
    if not exists('data'):
        mkdir('data')
    for i, s in enumerate(sample):
        print(f'\nDownloading data for sub-{s}: {i+1} out of {len(sample)}.')
        sp.run(f'python copy_dwi.py {s} {args.dir} data -v', shell=True)
else:
    print('Data will not be copied.')

# Run the test for both orders:
for o in [1,2]:
    for i, s in enumerate(sample):
        print(f'\nRunning the test: Order {o} for sub-{s}: {i+1} out of {len(sample)}.')
        sp.run(f'python run_denoise.py {s} {o}', shell=True)
