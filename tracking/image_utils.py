import os
from typing import List, Iterator

from PIL import Image, ImageSequence
import numpy as np

from tracking.models import ApplicationError

# Normalizes to uint8 ndarray
def normalize(data: np.ndarray, as_type=np.uint8) -> np.ndarray:
    if data.dtype == np.uint8:
        return data.astype(as_type, copy=False)
    elif np.can_cast(data.dtype, np.uint8, casting='safe'):
        return data.astype(as_type, copy=False)
    else:
        amax = data.max()
        amin = data.min()
        if amax - amin == 0:
            return np.full(data.shape, min(abs(int(data[0, 0])), 255))
        else:
            ret = (data - amin) / (amax - amin) * 255
            return ret.astype(as_type, copy=False)

def to_bw(data: np.ndarray) -> np.ndarray:
    shape = data.shape
    if len(shape) == 2:
        return data
    elif len(shape) == 3:
        if shape[2] == 1:
            return data.squeeze(axis=2)
        else:
            if shape[2] == 4:
                # rgba -> Ignoramos alpha
                data = np.delete(data, 3, axis=2)
            if shape[2] == 3 or shape[2] == 4:
                # b = r/3 + g/3 + b/3
                return np.sum(data / 3, axis=2)

    raise ValueError(f'Unknown image shape: {shape}')

def img_to_8bit_array(img) -> np.ndarray:
    return normalize(to_bw(np.asarray(img)), np.uint8)

def frames_iterator(files, allowed_ext: List[str]) -> Iterator[np.ndarray]:
    for file in files:
        name: str
        ext: str
        name, ext = os.path.splitext(file.filename)
        ext = ext.lower()

        if ext not in allowed_ext:
            raise ApplicationError(f'file {file.filename} extension is not supported')

        if ext == '.raw':
            # We take shape from name using raw naming scheme: {name}-{height}_{width}_{channels}
            shape = tuple(map(int, name[name.rindex('-'):].split('_')))
            img = np.fromfile(file, dtype=np.uint8).reshape(shape)
            yield img_to_8bit_array(img)
        else:
            img = Image.open(file)
            if img.format == 'TIFF' and img.n_frames > 1:  # If there is more than 1 frame, it's a multi tiff image
                for frame in ImageSequence.Iterator(img):
                    yield img_to_8bit_array(frame)
            else:
                yield img_to_8bit_array(img)
