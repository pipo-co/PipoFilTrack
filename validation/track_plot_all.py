#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt

from validation_utils import load_tsv

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

def plot_error_bars(ax, x, y_mean, y_std, label, color, marker):
    ax.errorbar(
        x
        , y_mean
        # We use the standard error: std/sqrt(N)
        , yerr=y_std / np.sqrt(len(y_std))
        , capsize=2
        , fmt=marker
        , label=label
        , color=color
        , ecolor=color
    )

def load_data(target):
    sigmas = load_tsv(f'{target}/sigma_data.tsv')
    snrs = load_tsv(f'{target}/snr_data.tsv')
    errors = load_tsv(f'{target}/error_data.tsv')
    times = load_tsv(f'{target}/time_data.tsv')

    return {
        'sigmas':       sigmas,
        'snrs_mean':    snrs[:, 0],
        'snrs_std':     snrs[:, 1],
        'errors_mean':  errors[:, 0],
        'errors_std':   errors[:, 1],
        'times_mean':   times[:, 0],
        'times_std':    times[:, 1],
    }

plots = [
    {
        'label': 'Lineal',
        'color': '#e41a1c',
        'marker': 'o',
        'data': load_data('linear')
    },
    {
        'label': 'Lineal Grande',
        'color': '#377eb8',
        'marker': 'o',
        'data': load_data('linear-big')
    },
    {
        'label': 'Curvo',
        'color': '#4daf4a',
        'marker': 'o',
        'data': load_data('sin')
    }
]

# Plot: RMSE vs SNR
ax = ax_init('Root Mean Square Error [pixel]', 'Signal to Noise Ratio (SNR)')
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['errors_mean'], data['errors_std'], plot['label'], plot['color'], plot['marker'])
ax.legend()

# Plot: SNR vs sigma
ax = ax_init('Signal to Noise Ratio (SNR)', 'Sigma')
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['sigmas'], data['snrs_mean'], data['snrs_std'], plot['label'], plot['color'], plot['marker'])
ax.legend()

# Plot: times vs SNR
ax = ax_init('Execution Time [millisecond]', 'Signal to Noise Ratio (SNR)')
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['times_mean'], data['times_std'], plot['label'], plot['color'], plot['marker'])
ax.legend()

# Render plots
plt.show()
