import argparse
from main import DwiPreprocessingClab

"""
Wrapper for running topup in multiple batches. Each batch runs on a separate thread
"""

args = argparse.ArgumentParser()
args.add_argument('input', type=str, required=True, help='Input CSV file')
args.add_argument('taks', type=str, required=True, help='Task name')
args.add_argument('-w', '--wait', type=int, default=0, help='Wait time')
args = argparse.parse_args()

p = DwiPreprocessingClab(task=args.task, mode='l',\
    input=args.input, \
    datain='/mnt/nasips/COST_mri/derivatives/dwi/',\
    dataout='/mnt/nasips/COST_mri/derivatives/dwi/')

p.topup(skip_processed=True, wait=args.wait)