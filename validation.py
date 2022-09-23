from typing import Tuple, Union

import numpy as np
from PIL import Image as PImage
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot as plt

from numpy.lib.stride_tricks import sliding_window_view

from tracking.image_utils import normalize
from tracking.main import track_filament
from tracking.models import Config

# Le podemos setear la seed
rng: np.random.Generator = np.random.default_rng()

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

def main():
    # Image properties
    width   = 166
    height  = 96

    # global sampling
    runs = 50

    # Filament properties
    thickness = 3
    max_value = 150

    # Filament function
    def f(x):
        # return np.round(height/width * x).astype(np.uint8)                    # Linear
        return (height/4 * np.sin(10/width * x) + height/2).astype(np.uint8)    # Sen

    # Filament softening (gaussian convolution) properties
    conv_sigma          = 10
    conv_kernel_size    = 3

    # Noise (gaussian) properties
    noise_percentage    = 85
    noise_sigma_start   = 0.0000  # Queremos variar el sigma del ruido
    noise_sigma_end     = 0.0060
    noise_sigma_step    = 0.0001

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
        bezier_segment_len  = 100,
        bezier_smoothing    = True,
    )

    # Calculate starting conditions
    x = np.arange(width - thickness)
    y = f(x)
    thick = (thickness - thickness % 2) // 2
    selected_points = np.dstack((x[trim_len:-trim_len:point_density], y[trim_len:-trim_len:point_density])).squeeze()

    noise_sigmas = np.linspace(noise_sigma_start, noise_sigma_end, num=int((noise_sigma_end - noise_sigma_start) // noise_sigma_step))
    errors = []

    # For each noise sigma
    for _ in range(runs):
        current_errors = []
        errors.append(current_errors)
        for noise_sigma in noise_sigmas:
            img = np.zeros((height, width))

            # Draw filament
            for offset in range(-thick, thick + 1):
                img[y + offset, x] = max_value
            img = gauss_convolution(img, conv_sigma, conv_kernel_size)
            img = gauss_noise(img, noise_sigma, noise_percentage)
            img = normalize(img)

            # Track
            result = track_filament((img,), selected_points, config)
            result_x = np.asarray([point.x for point in result.frames[0].points])
            result_y = np.asarray([point.y for point in result.frames[0].points])

            # Mean Square Error
            mse = mean_squared_error(f(result_x), result_y)
            current_errors.append(mse)

            # Debug output
            point_count = len(result.frames[0].points)
            inter_count = len([point for point in result.frames[0].points if point.status is not None])
            print(f'Sigma: {noise_sigma:.4f}, MSE: {mse}, Interpolated: {inter_count}/{point_count}')
            PImage.fromarray(img).save(f'validations/test-{noise_sigma:.4f}.png')

    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(1, 1, 1)

    e = np.array(errors)

    ax.errorbar(
        noise_sigmas
        , np.mean(e, axis=0)
        , yerr=np.std(e, axis=0)
        , capsize=2
    )
    ax.set_yscale('log')
    ax.grid(which="both")


    fig = plt.figure(2, figsize=(16, 10))
    ax = fig.add_subplot(1, 1, 1)
    # Plot sigma vs error
    for i in range(runs):
        ax.plot(noise_sigmas, errors[i])
    
    ax.grid(which="both")

    plt.show()

def cross_main():
    # Image properties
    width   = 166
    height  = 96

    # global sampling
    runs = 50

    # Filament properties
    thickness = 3
    max_value = 150
    angle_start = 10
    angle_end = 60

    # Filament softening (gaussian convolution) properties
    conv_sigma          = 10
    conv_kernel_size    = 3

    # Noise (gaussian) properties
    noise_percentage    = 85
    noise_sigma         = 0.001

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
        bezier_segment_len  = 100,
        bezier_smoothing    = True,
    )

    # Calculate starting conditions
    x = np.arange(thickness, width - thickness)
    thick = (thickness - thickness % 2) // 2

    angles = np.linspace(angle_start, angle_end, num=angle_end - angle_start + 1)
    errors = []

# For each noise sigma
    for _ in range(runs):
        current_errors = []
        errors.append(current_errors)
        for angle in angles:
            # Filament function
            m = np.tan(np.deg2rad(angle / 2))
            mid_y = m * width / 2
            off = height / 2 - mid_y

            def f(x):
                return np.round(m * x + off).astype(np.uint8)

            def g(x):
                return height - 1 - np.round(m * x + off).astype(np.uint8)

            y = f(x)
            y2 = g(x)
            img = np.zeros((height, width))
            selected_points = np.dstack((x[trim_len:-trim_len:point_density], y[trim_len:-trim_len:point_density])).squeeze()

            # Draw filament
            for offset in range(-thick, thick + 1):
                img[y + offset, x] = max_value
                img[y2 + offset, x] = max_value
            img = gauss_convolution(img, conv_sigma, conv_kernel_size)
            img = gauss_noise(img, noise_sigma, noise_percentage)
            img = normalize(img)

            # Track
            result = track_filament((img,), selected_points, config)
            result_x = np.asarray([point.x for point in result.frames[0].points])
            result_y = np.asarray([point.y for point in result.frames[0].points])

            # Mean Square Error
            mse = mean_squared_error(f(result_x), result_y)
            current_errors.append(mse)

            # Debug output
            point_count = len(result.frames[0].points)
            inter_count = len([point for point in result.frames[0].points if point.status is not None])
            print(f'Angle (deg): {int(angle)}, MSE: {mse}, Interpolated: {inter_count}/{point_count}')
            PImage.fromarray(img).save(f'validations/cross-angle-{int(angle)}.png')

    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(1, 1, 1)

    e = np.array(errors)

    ax.errorbar(
        angles
        , np.mean(e, axis=0)
        , yerr=np.std(e, axis=0)
        , capsize=2
    )
    ax.set_yscale('log')
    ax.grid(which="both")


    fig = plt.figure(2, figsize=(16, 10))
    ax = fig.add_subplot(1, 1, 1)
    # Plot sigma vs error
    for i in range(runs):
        ax.plot(angles, errors[i])
    
    ax.grid(which="both")

    plt.show()

if __name__ == '__main__':
    cross_main()

