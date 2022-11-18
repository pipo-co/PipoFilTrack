#!/usr/bin/env python

import sys
sys.path.insert(1, '../')

import time

import numpy as np
from PIL import Image as PImage
from sklearn.metrics import mean_squared_error

from tracking.image_utils import normalize
from tracking.main import track_filament
from tracking.models import Config

from validation_utils import set_seed, gauss_convolution, gauss_noise, save_as_tsv

# --- Validation Config --- #

# Output config
target = 'linear'

# Seed
seed = time.time_ns()

# Image properties
width   = 166
height  = 96

# Global sampling
runs = 50

# Filament properties
thickness = 3
max_value = 150

# Filament function
def f(x):
    return np.round(height/width * x).astype(np.uint8)  # Linear
    # return (height/4 * np.sin(10/width * x) + height/2).astype(np.uint8)  # Sin

# Filament softening (gaussian convolution) properties
conv_sigma          = 10
conv_kernel_size    = 3

# Noise (gaussian) properties
noise_percentage    = 85
noise_sigma_start   = 0.0001
noise_sigma_end     = 0.0060
noise_sigma_step    = 0.0001

# Image background limits (for SNR)
bg_y_start    = 50
bg_y_end      = 70
bg_x_start    = 10
bg_x_end      = 30

# Point selection
trim_len        = 20
point_density   = 15

# Tracking config
config = Config(
    max_fitting_error   = 0.6,
    normal_line_length  = 10,
    point_density       = 1,
    missing_inter_len   = 3,
    max_tangent_length  = 15,
    bezier_segment_len  = 500,
    bezier_smoothing    = True,
)

# --- Start Validation --- #

set_seed(seed)

# Calculate starting conditions
x = np.arange(width - thickness)
y = f(x)
thick = (thickness - thickness % 2) // 2
selected_points = np.dstack((x[trim_len:-trim_len:point_density], y[trim_len:-trim_len:point_density])).squeeze()
noise_sigmas    = np.linspace(noise_sigma_start, noise_sigma_end, num=int((noise_sigma_end - noise_sigma_start) // noise_sigma_step))
snrs            = []
errors          = []
times           = []

# For each noise sigma
for noise_sigma in noise_sigmas:
    img_to_save = None

    current_snrs = []
    snrs.append(current_snrs)

    current_errors = []
    errors.append(current_errors)

    current_times = []
    times.append(current_times)

    # For each run
    for run in range(runs):
        # Build image
        img = np.zeros((height, width))
        for offset in range(-thick, thick + 1):
            img[y + offset, x] = max_value
        img = gauss_convolution(img, conv_sigma, conv_kernel_size)
        img = gauss_noise(img, noise_sigma, noise_percentage)
        img = normalize(img)
        img_to_save = img

        # Track
        runtime = time.perf_counter()
        result = track_filament((img,), selected_points, config).frames[0]
        runtime = 1000 * (time.perf_counter() - runtime)
        result_x = np.asarray([point.x for point in result.points])
        result_y = np.asarray([point.y for point in result.points])
        current_times.append(runtime)

        # Signal to Noise Ratio [Dimensionless]
        bg      = img[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
        signal  = np.mean(np.stack([img[y + offset, x] for offset in range(-thick, thick + 1)])) - np.mean(bg)
        noise   = np.std(bg)
        snr     = signal / noise
        current_snrs.append(snr)

        # Root Mean Square Error [Pixel]
        rmse = np.sqrt(mean_squared_error(f(result_x), result_y))
        current_errors.append(rmse)

        # Console output
        point_count = len(result.points)
        inter_count = len([point for point in result.points if point.status is not None])
        print(
            f'| sigma: {noise_sigma:<8.4f} '
            f'| run: {run:<2} '
            f'| signal: {signal:<8.4f} '
            f'| noise: {noise:<8.4f} '
            f'| SNR: {snr:<8.4f} '
            f'| RMSE: {rmse:<13.10f} '
            f'| time: {runtime:<7.2f} '
            f'| Interpolated: {inter_count:>3}/{point_count:<3} '
            f'|'
        )

    # Save image representing current sigma
    PImage.fromarray(img_to_save).save(f'{target}/imgs/{noise_sigma:.4f}.png')

snrs    = np.array(snrs)
errors  = np.array(errors)
times   = np.array(times)

# We want to store mean and std
sigma_data  = (noise_sigmas,)
snr_data    = (np.mean(np.array(snrs),  axis=1), np.std(snrs,   axis=1))
error_data  = (np.mean(np.array(errors),axis=1), np.std(errors, axis=1))
time_data   = (np.mean(np.array(times), axis=1), np.std(times,  axis=1))

# Save data
print(f'{seed=}')
save_as_tsv(sigma_data, f'{target}/sigma_data.tsv', ('sigma',))
save_as_tsv(snr_data,   f'{target}/snr_data.tsv',   ('mean', 'std'))
save_as_tsv(error_data, f'{target}/error_data.tsv', ('mean', 'std'))
save_as_tsv(time_data,  f'{target}/time_data.tsv',  ('mean', 'std'))
