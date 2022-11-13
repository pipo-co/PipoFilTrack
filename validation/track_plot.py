#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt

from validation_utils import load_tsv

# Input config
target = 'linear'

# Plot config
figsize         = (16, 10)
label_text_size = 24
label_text_pad  = 10
label_tick_size = 16

def ax_init(y_label, x_label):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.tick_params(labelsize=label_tick_size)
    ax.set_ylabel(y_label, size=label_text_size, labelpad=label_text_pad)
    ax.set_xlabel(x_label, size=label_text_size, labelpad=label_text_pad)
    return ax

def plot_error_bars(ax, x, y_mean, y_std):
    ax.errorbar(
        x
        , y_mean
        # We use the standard error: std/sqrt(N)
        , yerr=y_std / np.sqrt(len(y_std))
        , capsize=2
        , fmt='o'
    )

# Load data
sigmas  = load_tsv(f'{target}/sigma_data.csv')
snrs    = load_tsv(f'{target}/snr_data.csv')
errors  = load_tsv(f'{target}/error_data.csv')
times   = load_tsv(f'{target}/time_data.csv')

snrs_mean   = snrs[:, 0]
snrs_std    = snrs[:, 1]
errors_mean = errors[:, 0]
errors_std  = errors[:, 1]
times_mean  = times[:, 0]
times_std   = times[:, 1]

# Plot: RMSE vs SNR
ax = ax_init('Root Mean Square Error [pixel]', 'Signal to Noise Ratio (SNR)')
plot_error_bars(ax, snrs_mean, errors_mean, errors_std)

# Plot: SNR vs sigma
ax = ax_init('Signal to Noise Ratio (SNR)', 'Sigma')
plot_error_bars(ax, sigmas, snrs_mean, snrs_std)

# Plot: times vs SNR
ax = ax_init('Execution Time [millisecond]', 'Signal to Noise Ratio (SNR)')
plot_error_bars(ax, snrs_mean, times_mean, times_std)

# Render plots
plt.show()
