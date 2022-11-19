#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt

from validation_utils import load_tsv

# Input config
target = 'inter'

# Axis config
figsize         = (16, 10)
label_text_size = 40
label_text_pad  = 15
label_tick_size = 30

margins_config = {
    'left': 0.105,
    'right': 0.98,
    'top': 0.97,
    'bottom': 0.125,
}

# Marker config
marker_size = 10
line_style  = ''
fill_style  = None

# Load data
angles  = load_tsv(f'{target}/angle_data.tsv')
errors  = load_tsv(f'{target}/error_data.tsv')

errors_mean = errors[:, 0]
errors_std  = errors[:, 1]

# Plot: RMSE vs angle
fig = plt.figure(figsize=figsize)
ax = fig.add_subplot(1, 1, 1)
ax.grid(which="both")
ax.tick_params(labelsize=label_tick_size)
ax.set_ylabel('Root Mean Square Error [pixel]', size=label_text_size, labelpad=label_text_pad)
ax.set_xlabel('Intersection angle [deg]', size=label_text_size, labelpad=label_text_pad)
plt.subplots_adjust(**margins_config)
ax.errorbar(
    angles
    , errors_mean
    # We use the standard error: std/sqrt(N)
    , yerr=errors_std / np.sqrt(len(errors_std))
    , capsize=2
    , marker='o'
    , markersize=marker_size
    , linestyle=line_style
    , fillstyle=fill_style
)

# Render plots
plt.show()
