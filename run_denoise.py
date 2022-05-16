#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run DWI denoising using DIPY patch2self

Parameters
----------
see arguments below

Returns
-------
Results of called functions.


Created on Fri Apr 22 23:14:54 2022
@author: aleksander nitka
"""

import argparse
from os.path import exists
import numpy as np
from datetime import datetime as dt

args = argparse.ArgumentParser(description="Function to run denoising of the dwi data - implementation uses the patch2self from dipy 1.5.0.")
args.add_argument('-f', '--file', help='Provide a list of subjects in a csv format with one subject per line.', default=None)
args.add_argument('-s', '--sub', help='Provide a single subject ID.', default=None)
args.add_argument('-t', '--telegram', help='Enables notifications with telegram, must have send_telegram.py file with bot configs on the same level.', default=False, action='store_true')
args.add_argument('-r', '--rawdir', help='Specify the input dir; it is usually the rawdata dir with all the sub dirs inside which I will find dwi dir with all the dwi files.', required=True)
args.add_argument('-o', '--out', help='Specify outdir, where the denoised data will be saved, a sub dir will be created there.', required=True)
args.add_argument('-l', '--log', help='Save a simple log of what has been processed.', default=False, action='store_true')
args.add_argument('-c', '--cp', help='Copy data from rawdir, if set as False the data will not be copied - all data required is in tmp already', required=False, default=True, action='store_false')
args.add_argument('--noclean', help='Do not clean the tmp folder after denoising has been completed', default=False, action='store_true')
args.add_argument('--nomove', help='Do not clean the tmp folder and do not move to out dir after denoising', default=False, action='strore_true')
args = args.parse_args()

def denoise_me(s, copy_dwi = args.cp, log = args.log, rawdir = args.rawdir, outdir = args.out, no_clean = args.noclean, no_move = args.nomove):
    """
    Perform copying (if needed), gradients estimation and denoising with p2s
    Set for a single ss but when list given just embed this fn in a loop.
    """
    from dwiprep import cp_dwi_files, rm_noise_p2s, mk_gradients
    import subprocess as sb
    from os import mkdir
    from os.path import join, exists
    from datetime import datetime as dt

    if copy_dwi is True and exists(join(rawdir, s, 'dwi')) is True:
        try:
            mkdir(join('tmp', s))
            # Copy all required files
            cp_dwi_files(s, rawdir, f'tmp/{s}')
        except:
            print(f'{dt.now()} {s} error while copying dwi files - dwi files are missing or tmp/{s} has already been created.')
            if log:
                with open('denoise_errors.log', 'a') as e:
                    e.write(f'{dt.now()}\t{s}\terror copying dwi files\n')
                    e.close()
            return None
    else:
        try:
        # Make gradients
        mk_gradients(s)

    # Denoise p2s
    rm_noise_p2s(s)

    # Sort and move files to derivatives directory
    # move files to derivatives directory
    if no_move is False:
        sb.run(f'cp -r tmp/{s} {outdir}{s}', shell = True)
    else:
        print(f'{dt.now()} {s} data not moved to the outdir (--nomove flag)')

    if no_clean is False:
        sb.run(f'rm -rf tmp/{s}', shell = True)
    else:
        print(f'{dt.now()} {s} data not removed from the tmpdir (--noclean flag)')

    if log:
        with open('denoise_done.log', 'a') as l:
            l.write(f'{dt.now()}\t{s}\tdenoised\n')
            l.close()

    return None


if args.file is args.sub is None:
    # raise error KILL
    # TODO
    pass
elif args.file is not None and args.sub is not None:
    # raise error KILL
    # TODO
    pass
elif args.file is not None:
    # run from list
    # TODO
    # Load the subject list
    subs = np.loadtxt(args.file, delimiter='\n', dtype=str)
    run_with = args.file
    pass
elif args.sub is not None:
    # run singe subject
    # TODO
    # add sub- prefix if missing
    if 'sub' not in args.sub:
        args.sub = 'sub-' + str(args.sub)
    run_with = args.sub
    pass

if args.telegram is True and exists('send_telegram.py'):
    from send_telegram import sendtel
    telegram = True
    sendtel(f'Denoising started for {run_with}')
else:
    telegram = False

print(f'Denoising started for {run_with}')



for idx, s in enumerate(subs):

    print(f'{s} -- {idx} out of {len(subs)}')

    # Perform checks



if telegram:
    sendtel(f'Denoising finished for {run_with}')
print(f'{dt.now()} Denoising finished for {run_with}')



