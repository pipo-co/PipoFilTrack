#!/usr/bin/env python

import time
from typing import Tuple, Union

import numpy as np
from PIL import Image as PImage
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot as plt

from numpy.lib.stride_tricks import sliding_window_view

from tracking.image_utils import normalize
from tracking.main import track_filament
from tracking.models import Config

# Seed can be hardcoded
seed: int = time.time_ns()
rng: np.random.Generator = np.random.default_rng(seed=seed)

def index_matrix(x: int, y: int) -> np.ndarray:
    return np.array(list(np.ndindex(x, y))).reshape((x, y, 2))

def gauss_kernel(kernel_size:int, sigma: float) -> np.ndarray:
    indices = index_matrix(kernel_size, kernel_size) - kernel_size//2
    indices = np.sum(indices**2, axis=2)
    indices = np.exp(-indices / sigma**2)
    return indices / (2 * np.pi * sigma**2)

def sliding_window(matrix: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    return sliding_window_view(np.pad(matrix, (shape[0] - 1) // 2, mode='constant', constant_values=0), shape)

def weighted_sum(channel: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    sw = sliding_window(channel, kernel.shape)
    return np.sum(sw[:, :] * kernel, axis=(2, 3))

def gauss_convolution(img: np.ndarray, sigma: float, kernel_size: int) -> np.ndarray:
    return weighted_sum(img, gauss_kernel(kernel_size, sigma))

# \frac{1}{\sqrt{ 2 \pi \sigma^2 }}e^{ - \frac{ (x - \mu)^2 } {2 \sigma^2} }
def gaussian(mu: float, sigma: float, size: int) -> Union[float, np.ndarray]:
    return rng.normal(mu, sigma, size)

def gauss_noise(img: np.ndarray, sigma: float, percentage: int) -> np.ndarray:
    p = percentage / 100
    n = int(img.size * p)
    shape = np.shape(img)
    indices = rng.choice(img.size, n, replace=False)
    ret = img.flatten()
    noise = gaussian(0, sigma, n)
    ret[indices] = ret[indices] + noise * 255
    return np.reshape(ret, shape)

def tracking_validation():
    # --- Validation Config --- #

    # Output config
    imgs_name   = 'linear'
    figsize     = (16, 10)

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

    # Calculate starting conditions
    x = np.arange(width - thickness)
    y = f(x)
    thick = (thickness - thickness % 2) // 2
    selected_points = np.dstack((x[trim_len:-trim_len:point_density], y[trim_len:-trim_len:point_density])).squeeze()
    noise_sigmas    = np.linspace(noise_sigma_start, noise_sigma_end, num=int((noise_sigma_end - noise_sigma_start) // noise_sigma_step))
    snrs            = []
    errors          = []

    # For each noise sigma
    for noise_sigma in noise_sigmas:
        img_to_save = None

        current_snrs = []
        snrs.append(current_snrs)

        current_errors = []
        errors.append(current_errors)

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
            result = track_filament((img,), selected_points, config).frames[0]
            result_x = np.asarray([point.x for point in result.points])
            result_y = np.asarray([point.y for point in result.points])

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
                f'| Interpolated: {inter_count:>3}/{point_count:<3} '
                f'|'
            )

        # Save image representing current sigma
        PImage.fromarray(img_to_save).save(f'validations/{imgs_name}-{noise_sigma:.4f}.png')

    snrs    = np.array(snrs)
    errors  = np.array(errors)

    # Plot: RMSE vs SNR
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.set_ylabel('Root Mean Square Error [pixel]')
    ax.set_xlabel('Signal to Noise Ratio (SNR)')
    ax.errorbar(
        np.mean(snrs, axis=1)
        , np.mean(errors, axis=1)
        # We use the standard error: std/sqrt(N)
        , yerr=np.std(errors, axis=1)/np.sqrt(len(errors))
        , capsize=2
        , fmt='o'
    )

    # Plot: SNR vs sigma
    fig = plt.figure(2, figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.set_ylabel('Signal to Noise Ratio (SNR)')
    ax.set_xlabel('Sigma')
    ax.errorbar(
        noise_sigmas
        , np.mean(snrs, axis=1)
        # We use the standard error: std/sqrt(N)
        , yerr=np.std(snrs, axis=1)/np.sqrt(len(snrs))
        , capsize=2
        , fmt='o'
    )

    # Output data
    print(snrs)
    print(errors)

    # Render plots
    plt.show()

def intersection_validation():
    # --- Validation Config --- #

    # Output config
    imgs_name   = 'inter'
    figsize     = (16, 10)

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
        PImage.fromarray(img_to_save).save(f'validations/{imgs_name}-{int(angle)}.png')

    errors = np.array(errors)

    # Plot: RMSE vs angle
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(which="both")
    ax.set_ylabel('Root Mean Square Error [pixel]')
    ax.set_xlabel('Intersection angle [deg]')
    ax.errorbar(
        angles
        , np.mean(errors, axis=1)
        # We use the standard error: std/sqrt(N)
        , yerr=np.std(errors, axis=1)/np.sqrt(len(errors))
        , capsize=2
        , fmt='o'
    )

    # Output data
    print(f'{snr=}')
    print(angles)
    print(errors)

    # Render plots
    plt.show()

if __name__ == '__main__':
    tracking_validation()
    print(f'{seed=}')
