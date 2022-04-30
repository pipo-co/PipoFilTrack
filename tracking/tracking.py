from typing import List, Union
import math
import numpy as np

from tracking.types_utils import Point
from itertools import tee


def circle_coordinate(start: Point, angle: float, radius: float) -> Point:
    """
        Returns a new point that is the result of traversing from `start`,
         in the direction of `angle` for distance `radius`
    """
    x = start.x + math.cos(angle) * radius
    y = start.y + math.sin(angle) * radius
    return Point(int(x), int(y))

def threes(iterator):
    """
        Given the list [s0, s1, ...], returns an iterator that returns sets
         of three consecutive values. Ex: (s0,s1,s2), (s1,s2,s3), ...
    """
    a, b, c = tee([None] + iterator + [None], 3)
    next(b, None)
    next(c, None)
    next(c, None)
    return zip(a, b, c)


def get_line_angle(p1: Point, p2: Point) -> Union[float, None]:
    """
        Returns the angle between line from (p1.x, p1.y) -> (p2.x, p1.y) and
         the line formed by p1 and p2.
        (angles start at 0 to the right and get bigger in the
         clockwise direction)
    """
    if p1 is None or p2 is None:
        a = None
    else:
        a = math.atan2((p2.y-p1.y), (p2.x-p1.x))

    return a


def get_line_points(start_point: Point, amount: int, length: float, angle: float) -> List:
    """
        Returns `amount` equidistant points along the line described by `angle`, `length` and `start_point`
        (along with each point's distance to the center)
    """
    # TODO(WARNING): no son siempre centrados. Ej para un largo 10 y amount 5 devuelve [0,2,4,6,8]
    #  No deberia ser problema con amount grandes como se piensa usar (>100)
    lengths = [(a/amount-1/2)*length for a in range(amount)]
    
    return [{'point': circle_coordinate(start_point, angle, l), 'dist': l} for l in lengths]


def bright_score(point: Point, img, dist, max_len) -> float:
    bright_weight = 0.75
    br_score = point.brightness(img)/255.0
    dst_score = 1-abs(dist / max_len)
    return br_score * bright_weight + dst_score * (1 - bright_weight)


def get_brightest_point(start_point: Point, amount: int, length: float, angle: float, img) -> Point:
    line_points = get_line_points(start_point, amount, length, angle)

    brightest = {'point': start_point, 'score': bright_score(start_point, img, 0, length/2)}
    for p in line_points:
        point_score = bright_score(p['point'], img, p['dist'], length/2)
        if point_score > brightest['score']:
            brightest = {'point': p['point'], 'score': point_score}
    return brightest['point']


def adjust_point(point: Point, test_points_amount: int, recursion_depth: int, normal_len: float, normal_angle: float, img) -> Point:
    """
        Return brightest point along the normal line.
        Steps:
            1. Create an intensity profile for the normal line (grab equidistant points and record their brightness)
            2. Select the brightest point
            3. Optional recursive step: Repeat 1 and 2 starting from the point selected at 2 and with a smaller length
    """
    brightest_point = point
    
    for _ in range(recursion_depth):
        brightest_point = get_brightest_point(brightest_point, test_points_amount, normal_len, normal_angle, img)
        normal_len /= test_points_amount
    
    return brightest_point

def adjust_points(img, points: np.ndarray, normal_len: float) -> np.ndarray:
    """
        Steps. For each point:
            1 Find normal (tangent + 90 degrees) of line
            2 From a normal line of length `normal_len` centered on the filament line test the brightness
                of `test_points_amount` points
            3 From the brightest point, start another local search to again find the brightness point
            4 Repeat steps 2 and 3 `search_iterations` times
            5 At the end of the search, append the new point to new_points
    """
    # TODO(tobi): normal_len deberia estar estar expresado en pixeles??
    # Configuration
    # TODO(FIP6): find way to calculate velocity using previous movements and have normal_len depend on it (bigger velocity, bigger normal_len)
    #  This would help avoid losing a fast moving the filament.
    #  Alternative: using the velocity make a better guess of the next filament center and start searching there (don't change normal_len)

    # TODO(tobi): pasar el algoritmo a ndarray. Por ahora hacemos la traduccion de manera interna
    points = [Point(x, y) for x, y in points]

    test_points_amount = 250
    recursion_depth = 1

    new_points = []
    for left_p, p, right_p in threes(points):
        if left_p is None:
            normal_angle = get_line_angle(p, right_p) + math.pi/2
        elif right_p is None:
            normal_angle = get_line_angle(p, left_p) + math.pi/2
        else:
            # TODO(tobi): Yo haria el promedio entre [left_p, p] y [p, right_p]
            normal_angle = get_line_angle(left_p, right_p) + math.pi/2

        new_point = adjust_point(p, test_points_amount, recursion_depth, normal_len, normal_angle, img)
        new_points.append(new_point)

    return np.asarray([(p.x, p.y) for p in new_points])

