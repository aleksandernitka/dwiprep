#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Created on Tue May 31 13:48:53 2022
@author: aleksander nitka
"""

import argparse

args = argparse.ArgumentParser(description="Function collect and summarise all steps performed in the pre-processing stage; denoising, topup and eddy.")
args.add_argument('-l', '--list', help = 'CSV file containing subject ids.', required = True)
args.add_argument('-d', '--datain', help = 'Path where the data is stored.', required = True)
args = args.parse_args()

