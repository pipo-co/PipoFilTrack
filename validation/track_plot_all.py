#!/usr/bin/env python

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.container import ErrorbarContainer
from matplotlib.legend_handler import HandlerErrorbar

from validation_utils import load_tsv

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

legend_config = {
    'fontsize': 30,
    'markerscale': 2,
    'labelspacing': 0.8,
    'handler_map': {
        ErrorbarContainer: HandlerErrorbar(xerr_size=0.5),
    },
}

def ax_init(y_label, x_label):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.tick_params(labelsize=label_tick_size)
    ax.set_ylabel(y_label, size=label_text_size, labelpad=label_text_pad)
    ax.set_xlabel(x_label, size=label_text_size, labelpad=label_text_pad)
    plt.subplots_adjust(**margins_config)
    return ax

def plot_error_bars(ax, x, y_mean, y_std, label, color, marker):
    ax.errorbar(
        x
        , y_mean
        # We use the standard error: std/sqrt(N)
        , yerr=y_std / np.sqrt(len(y_std))
        , capsize=2
        , marker=marker
        , markersize=marker_size
        , linestyle=line_style
        , fillstyle=fill_style
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
labels = ('Root Mean Square Error [pixel]', 'Signal to Noise Ratio (SNR)')
ax = ax_init(*labels)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['errors_mean'], data['errors_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=1, right=5)
ax.set_ylim(top=1.6, auto=True)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['errors_mean'], data['errors_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)

# Plot: SNR vs sigma
labels = ('Signal to Noise Ratio (SNR)', 'Sigma')
ax = ax_init(*labels)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['sigmas'], data['snrs_mean'], data['snrs_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=0, right=0.0062)
ax.set_ylim(bottom=-0.2, top=10)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['sigmas'], data['snrs_mean'], data['snrs_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)

# Plot: times vs SNR
labels = ('Execution Time [millisecond]', 'Signal to Noise Ratio (SNR)')
ax = ax_init(*labels)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['times_mean'], data['times_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)
# Zoom
ax = ax_init(*labels)
ax.set_xlim(left=1, right=10)
ax.set_ylim(top=300, auto=True)
for plot in plots:
    data = plot['data']
    plot_error_bars(ax, data['snrs_mean'], data['times_mean'], data['times_std'], plot['label'], plot['color'], plot['marker'])
ax.legend(**legend_config)

# Render plots
plt.show()
