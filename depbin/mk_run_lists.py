#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from os import listdir as ls
from itertools import islice

argparser = argparse.ArgumentParser(description='Because some of the fsl functions are not paralelised, to speed things up, it would be beneficial if things are run concurently using multiple proccessing lists. This fn creates N-number of lists of all but last one are of specified len.') 

argparser.add_argument('subdir', type=str, help='The directory to create the lists from. Must contin sub-x directories.')
argparser.add_argument('N', type=int, help='Number of subjects per list.')
argparser.add_argument('-o', '--outdir', type=str, help='Output directory. Default is tmp.', default='tmp')
argparser.add_argument('-v', '--verbose', action='store_true', help='Print information about the lists.')
argparser.add_argument('-d', '--dryrun', action='store_true', help='Dry run. Do not create the lists. Just verbose.')
argparser.add_argument('-p', '--prefix', type=str, help='Prefix for the list files. Default is runList.', default='runList')
args = argparser.parse_args()

"""
Created on Fri Apr 22 10:37:14 2022
@author: aleksander nitka

"""

subs = [f for f in ls(args.subdir) if f.startswith('sub-')]
subs.sort()

# list to hold required lens for each list
lens = []
# keep the tally up
totaln = len(subs)

if args.verbose or args.dryrun:
    print('Total number of subjects:', totaln)

# add list len untill len is less than the list len
while totaln > args.N:
    lens.append(args.N)
    totaln = totaln - args.N
lens.append(totaln)
totaln = totaln - totaln # Should 0

# this should generate list of lists
it = iter(subs)
outputs = [list(islice(it, elem)) for elem in lens]

# for each sub-list write a file
for i, l in enumerate(outputs):
    if args.dryrun or args.verbose:
        print(f'List {i} has {len(l)} subjects. --> {args.outdir}/{args.prefix}_{i}.csv')
    if not args.dryrun:
        with open(f'{args.outdir}/{args.prefix}_{i}.csv', 'w') as f:
            # each subjects needs to be written to a file
            for j in outputs[i]:
                f.write(f'{j}\n')
            f.close()
