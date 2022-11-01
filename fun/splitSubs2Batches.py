import argparse
"""
This script splits the list of all subjects into batches of the
specified size.
"""

parser = argparse.ArgumentParser(description='Split subtitles into batches')
parser.add_argument('input', help='input file with all subs')
parser.add_argument('prefix', help='Prefix for each file')
parser.add_argument('batchSize', help='Number of subs per batch', type=int)
args = parser.parse_args()

with open(args.input, 'r') as f:
    lines = f.readlines()
    f.close()

for i in range(0, len(lines), args.batchSize):
    with open(args.prefix + str(i) + '.csv', 'w') as f:
        f.writelines(lines[i:i+args.batchSize])
        f.close()

        