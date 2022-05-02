#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Created on Mon May  2 16:13:11 2022
@author: aleksander nitka
"""

import pandas as pd
from os.path import join
import matplotlib.pyplot as plt

ddir = 'denoise_exp_results'

mdf = pd.read_csv(join(ddir, 'denoising_exp_results_mean.csv'))
sdf = pd.read_csv(join(ddir, 'denoising_exp_results_std.csv'))

