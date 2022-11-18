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
target = 'inter'

# Seed
seed = time.time_ns()

# Image properties
width   = 166
height  = 96

# Global sampling
runs = 50

# Filament properties
thickness   = 3
max_value   = 150

# Intersection angle
angle_start = 10
angle_end   = 60
# Angle step is 1

# Filament softening (gaussian convolution) properties
conv_sigma          = 10
conv_kernel_size    = 3

# Noise (gaussian) properties
noise_percentage    = 85
noise_sigma         = 0.001

# Image background limits (for SNR just on first frame)
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
x       = np.arange(thickness, width - thickness)
thick   = (thickness - thickness % 2) // 2
angles  = np.linspace(angle_start, angle_end, num=angle_end - angle_start + 1)
errors  = []
snr     = None  # SNR of first frame (should always be the same)

# For each angle
for angle in angles:
    img_to_save = None

    current_errors = []
    errors.append(current_errors)

    # Filament function slope (m) and offset(off)
    m       = np.tan(np.deg2rad(angle / 2))
    mid_y   = m * width / 2
    off     = height / 2 - mid_y

    # For each run
    for run in range(runs):
        # Main filament function
        def f(x):
            return np.round(m * x + off).astype(np.uint8)

        # Intersecting filament function
        def g(x):
            return height - 1 - np.round(m * x + off).astype(np.uint8)

        # Create filaments and selected points
        y               = f(x)
        y2              = g(x)
        selected_points = np.dstack((x[trim_len:-trim_len:point_density], y[trim_len:-trim_len:point_density])).squeeze()

        # Build image
        img = np.zeros((height, width))
        for offset in range(-thick, thick + 1):
            img[y + offset, x]  = max_value
            img[y2 + offset, x] = max_value
        img = gauss_convolution(img, conv_sigma, conv_kernel_size)
        img = gauss_noise(img, noise_sigma, noise_percentage)
        img = normalize(img)
        img_to_save = img

        # Calculate SNR on first frame (should always be the same)
        if snr is None:
            bg = img[bg_y_start:bg_y_end, bg_x_start:bg_x_end]
            signal = np.mean(np.stack([img[y + offset, x] for offset in range(-thick, thick + 1)])) - np.mean(bg)
            noise = np.std(bg)
            snr = signal / noise

        # Track
        result = track_filament((img,), selected_points, config).frames[0]
        result_x = np.asarray([point.x for point in result.points])
        result_y = np.asarray([point.y for point in result.points])

        # Root Mean Square Error - Pixel Units
        rmse = np.sqrt(mean_squared_error(f(result_x), result_y))
        current_errors.append(rmse)

        # Console output
        point_count = len(result.points)
        inter_count = len([point for point in result.points if point.status is not None])
        print(
            f'| angle: {int(angle):<2} '
            f'| run: {run:<2} '
            f'| RMSE: {rmse:<13.10f} '
            f'| Interpolated: {inter_count:>3}/{point_count:<3} '
            f'|'
        )

    # Save image representing current angle
    PImage.fromarray(img_to_save).save(f'{target}/imgs/{int(angle)}.png')

errors = np.array(errors)

# We want to store mean and std
angle_data = (angles,)
error_data = (np.mean(np.array(errors), axis=1), np.std(errors, axis=1))

# Save data
print(f'{seed=}')
print(f'{snr=}')
save_as_tsv(angle_data, f'{target}/angle_data.tsv', ('angle',))
save_as_tsv(error_data, f'{target}/error_data.tsv', ('mean', 'std'))
