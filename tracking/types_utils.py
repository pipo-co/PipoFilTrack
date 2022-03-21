import numpy as np
from typing import List
import math


class Point:
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = int(x)
        self.y = int(y)

    def __repr__(self):
        return f'({self.x}, {self.y})'
    
    def out_of_bounds(self, img):
        y_limit, x_limit = img.shape
        return self.x >= x_limit or self.x < 0 or self.y >= y_limit or self.y < 0

    def is_wall(self, img) -> bool:
        return img[self.y, self.x] < 127  # pixel is black

    def brightness(self, img) -> float:
        if self.out_of_bounds(img):
            return 0
        return img[self.y, self.x]

    def __eq__(self, other):
        if not isinstance(other, Point):
            # don't attempt to compare against unrelated types
            return NotImplemented
        delta = 0.00001

        return abs(self.x - other.x) < delta and abs(self.y - other.y) < delta


class Conf:
    def __init__(self, start: Point, current_position: Point, end: Point, start_angle=0,
                 angle_aperture=math.pi / 2, angles_amount=15, max_step_size=8, img='', debug=False):
        self.start = start  # starting point for the path tracing
        self.current_position = current_position  # current point in the path tracing
        self.end = end
        self.current_angle = start_angle  # (0 means to the right, 90 down, 180 left, 270 up, etc)
        self.angle_aperture = angle_aperture
        self.max_step_size = max(max_step_size, 1)
        self.angles_amount = angles_amount  # qty of different paths to consider for the next step (best with 8 or more)
        self.img = img
        self.debug = debug

    def copy(self):
        return Conf(start=self.start, current_position=self.current_position, end=self.end, start_angle=self.current_angle,
                    max_step_size=self.max_step_size, angles_amount=self.angles_amount,
                    img=self.img, debug=self.debug)


class FilamentTree:
    def __init__(self, conf: Conf, parent=None):
        self.parent: FilamentTree = parent
        self.conf = conf.copy()
        self.points = [conf.start]
        self.debug_points = [conf.start]
        self.widths = []
        self.is_leaf = True