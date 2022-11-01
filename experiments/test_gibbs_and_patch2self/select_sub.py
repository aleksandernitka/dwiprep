import random
from os import listdir as ls
import argparse

args = argparse.ArgumentParser(description='Selects random ids for test. Can save output to a txt file.')
args.add_argument('dir', help='Data dir with subs')
args.add_argument('-n', '--n', help='Set sample size', required=True)
args.add_argument('-s', '--seed', help='Set seed for random sample.')
args.add_argument('-o', '--out', help='Write IDs to file.', action='store_true', default=False)
args = args.parse_args()

subs = [f for f in ls(args.dir) if 'sub-' in f]
print(f'found {len(subs)} ids.')

if args.seed:
    random.seed(args.seed)
samp = random.sample(subs, int(args.n))
print(f'Selected {args.n} IDs: {samp}')

if args.out:
    print('Saved to random_sample.txt.')
    with open('random_sample.txt', 'w') as f:
        for i in samp:
            f.writelines(f'{i.replace("sub-","")}\n')