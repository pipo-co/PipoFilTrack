from typing import List
import os
import re


def get_frame_identifiers(frames_folder: str) -> List[str]:
    frames = []
    
    for root, _, filenames in os.walk(frames_folder):
        if 'results' in root:
            continue
        for filename in sorted(filenames, key=lambda x: int(re.search(r'\d+', x).group())):
            if filename.endswith('.tif'):
                frames.append(os.path.join(root, filename))
    
    return frames