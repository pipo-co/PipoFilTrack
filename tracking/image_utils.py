import os
from typing import List, Iterator

from PIL import Image, ImageSequence
import numpy as np

from tracking.models import ApplicationError

# TODO(tobi): Soportar avi movies
# def convert_avi_to_tif(server_folder, complete_filename):
#     video = cv2.VideoCapture(complete_filename)
#
#     i = 0
#     while video.isOpened():
#         success, frame = video.read()
#         if not success:
#             break
#         filename = secure_filename(str(i) + '.tif')
#         complete_filename = '/'.join([server_folder, filename])
#         cv2.imwrite(complete_filename, frame)
#
#         img = Image.open(complete_filename)
#         if img.height != img.width:
#             img = resize_image(img, min(img.height, img.width))
#         img.save(complete_filename)
#
#         if i == 0:
#             save_first_frame_as_jpg(server_folder, filename, complete_filename)
#         i += 1
#
#     video.release()
#     cv2.destroyAllWindows()
#     # Delete the avi file because we already saved each frame
#     os.remove('/'.join([server_folder, '0.avi']))

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

# b = r/3 + g/3 + b/3
def to_bw(data: np.ndarray) -> np.ndarray:
    shape = data.shape
    if len(shape) == 3 and shape[2] == 3:
        return np.sum(data/3, axis=2)
    else:
        return data

def pil_to_8bit_array(img: Image) -> np.ndarray:
    return normalize(to_bw(np.asarray(img)), np.uint8)

def frames_iterator(files, allowed_ext: List[str]) -> Iterator[np.ndarray]:
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_ext:
            raise ApplicationError(f'file {file.filename} extension is not supported')

        if ext == '.avi':
            raise ApplicationError(f'avi files are not yet supported')

        img = Image.open(file)
        if img.n_frames > 1:  # If there is more than 1 frame, it's a multi tiff image
            for frame in ImageSequence.Iterator(img):
                yield pil_to_8bit_array(frame)
        else:
            yield pil_to_8bit_array(img)
