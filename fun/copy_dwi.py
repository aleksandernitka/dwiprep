import argparse
from os.path import join, exists
from os import mkdir
from os import listdir as ls
import shutil

args = argparse.ArgumentParser(description='Copy raw dwi files from directory to tmp directory where it can be processed further.')
args.add_argument('sub', help='subject id')
args.add_argument('dir', help='directory where dwis are')
args.add_argument('tmp', help='temp directory')
args.add_argument('-v', '--verbose', help='verbose', default=False, action='store_true')
args = args.parse_args()

if 'sub-' not in args.sub:
    args.sub = 'sub-' + str(args.sub)
       
# get all dwi files for pp
bfs = [f for f in ls(join(args.dir, args.sub, 'dwi')) if '.DS_' not in f]

# get all _AP_ files
fsdwi = [f for f in bfs if '_SBRef_' not in f and '_ADC_' not in f and '_TRACEW_' not in f and '_ColFA_' not in f and '_FA_' not in f]
if len(fsdwi) != 6:
    print(f'{args.sub} has {len} dwi files')
    exit()

if exists(join(args.tmp, args.sub)) is False:
    mkdir(join(args.tmp, args.sub))

# cp dwi to tmp
for f in fsdwi:
    if '_AP_' in f:
        fn = f'{args.sub}_AP.{f.split(".")[-1]}'
        if args.verbose:
            print(f'cp {join(args.dir, args.sub, "dwi", f)} ---> {join(args.tmp, args.sub, fn)}')
        shutil.copy(join(args.dir, args.sub, 'dwi', f), join(args.tmp, args.sub, fn))

    elif '_PA_' in f:
        fn = f'{args.sub}_PA.{f.split(".")[-1]}'
        if args.verbose:
            print(f'cp {join(args.dir, args.sub, "dwi", f)} ---> {join(args.tmp, args.sub, fn)}')
        shutil.copy(join(args.dir, args.sub, 'dwi', f), join(args.tmp, args.sub, fn))