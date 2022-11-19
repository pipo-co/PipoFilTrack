#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt

from validation_utils import load_tsv

# Input config
target = 'linear'

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

def ax_init(y_label, x_label):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.tick_params(labelsize=label_tick_size)
    ax.set_ylabel(y_label, size=label_text_size, labelpad=label_text_pad)
    ax.set_xlabel(x_label, size=label_text_size, labelpad=label_text_pad)
    plt.subplots_adjust(**margins_config)
    return ax

def plot_error_bars(ax, x, y_mean, y_std):
    ax.errorbar(
        x
        , y_mean
        # We use the standard error: std/sqrt(N)
        , yerr=y_std / np.sqrt(len(y_std))
        , capsize=2
        , marker='o'
        , markersize=marker_size
        , linestyle=line_style
        , fillstyle=fill_style
    )

# Load data
sigmas  = load_tsv(f'{target}/sigma_data.tsv')
snrs    = load_tsv(f'{target}/snr_data.tsv')
errors  = load_tsv(f'{target}/error_data.tsv')
times   = load_tsv(f'{target}/time_data.tsv')

snrs_mean   = snrs[:, 0]
snrs_std    = snrs[:, 1]
errors_mean = errors[:, 0]
errors_std  = errors[:, 1]
times_mean  = times[:, 0]
times_std   = times[:, 1]

# Plot: RMSE vs SNR
labels = ('Root Mean Square Error [pixel]', 'Signal to Noise Ratio (SNR)')
ax = ax_init(*labels)
plot_error_bars(ax, snrs_mean, errors_mean, errors_std)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=1, right=5)
ax.set_ylim(top=1.6, auto=True)
plot_error_bars(ax, snrs_mean, errors_mean, errors_std)

# Plot: SNR vs sigma
labels = ('Signal to Noise Ratio (SNR)', 'Sigma')
ax = ax_init(*labels)
plot_error_bars(ax, sigmas, snrs_mean, snrs_std)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=0, right=0.0062)
ax.set_ylim(bottom=-0.2, top=10)
plot_error_bars(ax, sigmas, snrs_mean, snrs_std)

# Plot: times vs SNR
labels = ('Execution Time [millisecond]', 'Signal to Noise Ratio (SNR)')
ax = ax_init(*labels)
plot_error_bars(ax, snrs_mean, times_mean, times_std)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=1, right=10)
ax.set_ylim(top=300, auto=True)
plot_error_bars(ax, snrs_mean, times_mean, times_std)

# Render plots
plt.show()
