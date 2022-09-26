import argparse
import pydicom
from os import listdir as ls
from os.path import join

args = argparse.ArgumentParser(description='Pull header info from a subject/sequence dir')
args.add_argument('dcmimage', help='Path to an image.')
args = args.parse_args()

f = [i for i in ls(args.dcmimage) if i.endswith('.IMA')]
f.sort()
file = f[0]

print(file)

data = pydicom.dcmread(join(args.dcmimage, file))
print('\n')
print(data['PatientName'])
print(data['PatientSex'])
print(data['PatientBirthDate'])
print(data['AcquisitionDate'])






