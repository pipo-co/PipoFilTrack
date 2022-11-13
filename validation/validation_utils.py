from typing import Tuple, Union

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

rng: np.random.Generator = np.random.default_rng()

def set_seed(seed: int):
    global rng
    rng = np.random.default_rng(seed=seed)

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

def save_as_tsv(data, filename, headers):
    np.savetxt(filename, np.dstack(data).squeeze(), header='\t'.join(headers), delimiter='\t', comments='')

def load_tsv(filename):
    return np.loadtxt(filename, delimiter='\t', skiprows=1)
