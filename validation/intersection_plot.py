#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt

from validation_utils import load_tsv

# Input config
target = 'inter'

# Plot config
figsize = (16, 10)
label_text_size = 24
label_text_pad = 10
label_tick_size = 16

# Load data
angles  = load_tsv(f'{target}/angle_data.csv')
errors  = load_tsv(f'{target}/error_data.csv')

errors_mean = errors[:, 0]
errors_std  = errors[:, 1]

# Plot: RMSE vs angle
fig = plt.figure(figsize=figsize)
ax = fig.add_subplot(1, 1, 1)
ax.grid(which="both")
ax.tick_params(labelsize=label_tick_size)
ax.set_ylabel('Root Mean Square Error [pixel]', size=label_text_size, labelpad=label_text_pad)
ax.set_xlabel('Intersection angle [deg]', size=label_text_size, labelpad=label_text_pad)
ax.errorbar(
    angles
    , errors_mean
    # We use the standard error: std/sqrt(N)
    , yerr=errors_std / np.sqrt(len(errors_std))
    , capsize=2
    , fmt='o'
)

# Render plots
plt.show()
