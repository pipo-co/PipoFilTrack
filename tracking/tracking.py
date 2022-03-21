from typing import List, Tuple, Union
import sys
import math
from scipy.signal import savgol_filter
import numpy as np

# Project imports
from tracking.types_utils import FilamentTree, Point, Conf
from itertools import tee


def circle_coordinate(start: Point, angle: float, radius: float) -> Point:
    """
        Returns a new point that is the result of traversing from `start`,
         in the direction of `angle` for distance `radius`
    """
    x = start.x + math.cos(angle) * radius
    y = start.y + math.sin(angle) * radius
    return Point(int(x), int(y))


def next_step(leaf: FilamentTree) -> Tuple[Union[Point, None], Union[float, None], float, List[FilamentTree]]:
    """
        Gets next point and angle for the tracking method using raytracing to
         try and stay in the center of the filament
         It will: cast rays in a given direction and keep the one with
         the tip closest to the center of the filament
        TODO(FIP1): this raycasting could be improved by casting less rays,
        keeping the best one and re-casting rays near the last selected one
        ("binary" search, x_nary search)
    """
    def distance_to_wall(point: Point, angle: float, distance_limit=200):
        """
            Returns distance to the nearest wall of a point in a given direction
        """
        # TODO: 200 seems like a big enough limit to check, but recheck for performance reasons
        length = 1
        wall_candidate = circle_coordinate(point, angle, length)
        for i in range(2, distance_limit):
            if wall_candidate.out_of_bounds(conf.img) or wall_candidate.is_wall(conf.img):
                break
            length = i
            wall_candidate = circle_coordinate(point, angle, length)

        # Uncomment to see all raycasts to the walls
        # if conf.debug and debug_points is not None:
        #     debug_points.append(point)
        #     debug_points.append(wall_candidate)
        #     debug_points.append(point)
        return length

    class NewPoint():
        def __init__(self, point=Union[Point, None], angle=Union[float, None], diff_to_walls=99999, dist_to_walls=0):
            self.point: Point = point
            self.angle: float = angle
            self.diff_to_walls: float = diff_to_walls
            self.dist_to_walls: float = dist_to_walls

    conf: Conf = leaf.conf
    debug_points: List[Point] = leaf.debug_points

    if conf.current_position is None or conf.angles_amount < 1 or conf.max_step_size < 1:
        raise ValueError('Wrong arguments for next_step')

    angles = [
        conf.current_angle + conf.angle_aperture *
        (a/conf.angles_amount - 0.5) for a in range(conf.angles_amount)
    ]

    candidates = []
    if conf.debug and debug_points is not None and len(debug_points) == 0:
        debug_points.append(conf.current_position)

    # iterated in reverse to avoid issues when removing angles from the list
    for angle in reversed(angles):

        # Find biggest radius possible for this angle
        point = None
        for radius in range(1, conf.max_step_size):
            aux = circle_coordinate(conf.current_position, angle, radius)
            if aux.out_of_bounds(conf.img) or aux.is_wall(conf.img):
                break
            point = aux
        if point is None:
            continue

        wall1 = distance_to_wall(point, angle + math.pi/2)
        wall2 = distance_to_wall(point, angle - math.pi/2)

        # measure of how centered the point is
        diff_to_walls = abs(wall1 - wall2)

        # measure of how big the tube is at that point
        dist_to_walls = wall1 + wall2

        candidates.append(NewPoint(point, angle, diff_to_walls, dist_to_walls))

        # Uncomment to see all raycasts considered
        if conf.debug and debug_points is not None:
            debug_points.append(point)
            debug_points.append(conf.current_position)

    # choose best next point yet
    scores = [candidate.diff_to_walls for candidate in candidates]
    scores = smooth_scores(smooth_scores(scores))
    chosen_candidates = []
    for i in range(len(scores)):
        if i != 0 and i != len(scores)-1 and scores[i-1] > scores[i] <= scores[i+1]:
            # Chooses candidates whose scores are local minimums
            chosen_candidates.append(candidates[i])

    if len(scores) != 0:
        if len(chosen_candidates) == 0:
            # If no local minimums, choose the global minimum
            chosen_candidates.append(candidates[np.where(scores == scores.min())[0][0]])

    if len(chosen_candidates) > 1:
        # Return bifurcation case
        children = []
        for candidate in chosen_candidates:
            conf1 = conf.copy()
            conf1.start = candidate.point
            conf1.current_position = candidate.point
            conf1.current_angle = candidate.angle
            child = FilamentTree(conf1, leaf)
            child.widths.append(candidate.dist_to_walls)
            children.append(child)
        
        return None, None, 0, children
    elif len(chosen_candidates) == 1:
        # Return normal case
        best_new_point = chosen_candidates[0]
        filament_width = best_new_point.dist_to_walls
        return best_new_point.point, best_new_point.angle, filament_width, []
    else:
        # Return error case
        return None, None, 0, []


def outline_filament(conf: Conf) -> Tuple[List[Point], List[Point], float]:
    """
        Tracks filament from a starting point in one direction
    """
    
    def calc_boundary_line(start, end):
        boundary_angle = get_line_angle(start, end) - math.pi / 2
        end_aux = circle_coordinate(end, boundary_angle, 100)
        l2 = np.array([end_aux.x, end_aux.y])
        l1 = np.array([end.x, end.y])
        return (l1, l2)

    def end_condition(current_point, boundary_line):
        # current_point is on the right side of the bounding line (bounding line is a
        #  line that crosses end and has an angle perpendicular to the one formed
        #  between start and end
        if current_point is None:
            return False

        p = np.array([current_point.x, current_point.y])
        return np.cross(boundary_line[1] - boundary_line[0], p - boundary_line[0]) > 0

    point = conf.start
    boundary_line = calc_boundary_line(conf.start, conf.end)
    
    filamentTreeLeafs: List[FilamentTree] = [FilamentTree(conf)]

    # Step 1: find possible branches
    for leaf in filamentTreeLeafs:
        while leaf.is_leaf and not end_condition(point, boundary_line):
            if leaf.conf.max_step_size <= 0:
                # Tried to increase step_size too many times, it's officially locked
                leaf.is_leaf = False
                break
            
            point, angle, width, children = next_step(leaf)

            # TODO(FIP4): maybe add regression if point is the same as
            #  last one (to avoid locking)
            if len(children) == 0:
                # acceptPointOrTryAgain(leaf, point, angle, width)
                if point is None or (len(leaf.points) > 0 and point == leaf.points[-1]):
                    # if locked, try again with a bigger step_size. WARNING: this
                    #  consumes one step (not a big issue)
                    # TODO(FIP5): maybe max_step_size should be per step, instead of globally be incrementing
                    leaf.conf.max_step_size -= 1
                else:
                    leaf.points.append(point)
                    leaf.widths.append(width)
                    leaf.conf.current_position = point
                    leaf.conf.current_angle = angle
            else:
                leaf.is_leaf = False
                # print([child.conf.current_position for child in children])
                for child in children:
                    # WARNING: not checking if point == last point. Not too bad, it will be checked next loop
                    filamentTreeLeafs.append(child)

    # Step 2: get best leaf (the one whose last position is closest to conf.end)
    best_filament = None
    min_dist = 999999
    print(f'Leafs percentage: {len([i for i in filter(lambda t: t.is_leaf, filamentTreeLeafs)])} / {len(filamentTreeLeafs)}')
    for filament in filter(lambda t: t.is_leaf, filamentTreeLeafs):
        curr = filament.conf.current_position
        dist = math.dist((curr.x, curr.y), (conf.end.x, conf.end.y))
        # print(f'{dist = }')
        if dist < min_dist:
            min_dist = dist
            best_filament = filament

    if best_filament is None or len(best_filament.widths) == 0:
        print('ERROR. Tracking returned 0 points')
        return [], [], 0
    
    # Step 3: get best leaf's entire branch (prepend ancestor's data to its own)
    ancestor = best_filament.parent
    while ancestor is not None:
        best_filament.points = ancestor.points + best_filament.points
        best_filament.debug_points = ancestor.debug_points + best_filament.debug_points
        best_filament.widths = ancestor.widths + best_filament.widths
        ancestor = ancestor.parent
    
    # For debugging purposes only (to get an idea of all paths considered)
    for filament in filamentTreeLeafs:
        ancestor = filament.parent
        while ancestor is not None:
            best_filament.debug_points = ancestor.debug_points + best_filament.debug_points
            ancestor = ancestor.parent

    # Step 4: return best branch
    avg_filament_width = sum(best_filament.widths) / len(best_filament.widths)
    return best_filament.points, best_filament.debug_points, avg_filament_width


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


adjust_debug_points = []


def adjust_points(img, points: List[Point], width: float) -> Tuple[List[Point], List[Point]]:
    """
        Steps. For each point:
            1 Find normal (tangent + 90 degrees) of line
            2 From a normal line of length `normal_len` centered on the filament line test the brightness
                of `test_points_amount` points
            3 From the brightest point, start another local search to again find the brightness point
            4 Repeat steps 2 and 3 `search_iterations` times
            5 At the end of the search, append the new point to new_points
    """
    # Configuration
    # TODO(FIP6): find way to calculate velocity using previous movements and have normal_len depend on it (bigger velocity, bigger normal_len)
    #  This would help avoid losing a fast moving the filament.
    #  Alternative: using the velocity make a better guess of the next filament center and start searching there (don't change normal_len)
    normal_len = float(2 * width)
    test_points_amount = 250
    recursion_depth = 1

    global adjust_debug_points
    adjust_debug_points = []
    new_points = []
    for left_p, p, right_p in threes(points):
        if left_p is None:
            normal_angle = get_line_angle(p, right_p) + math.pi/2
        elif right_p is None:
            normal_angle = get_line_angle(p, left_p) + math.pi/2
        else:
            normal_angle = get_line_angle(left_p, right_p) + math.pi/2
        adjust_debug_points.append(p)
        adjust_debug_points.append(circle_coordinate(p, normal_angle, normal_len/2))
        adjust_debug_points.append(p)
        adjust_debug_points.append(circle_coordinate(p, normal_angle + math.pi, normal_len/2))
        adjust_debug_points.append(p)

        new_point = adjust_point(p, test_points_amount, recursion_depth, normal_len, normal_angle, img)
        new_points.append(new_point)

    return new_points, adjust_debug_points


def smooth(points: List[Point]):
    # TODO: learn about window size to improve smoothing and avoid
    #  'If mode is 'interp', window_length must be less than or equal to the size of x.' error
    window_size = min(51, len(points))
    if window_size % 2 == 0:
        window_size -= 1  # must be odd number
    polynomial_order = min(3, window_size-1)
    # points_np = savgol_filter((zip(*points)), window_size, polynomial_order)
    points_np = savgol_filter(([p.x for p in points], [p.y for p in points]), window_size, polynomial_order)
    return [Point(p_np_x, p_np_y) for p_np_x, p_np_y in zip(points_np[0], points_np[1])]

def smooth_scores(scores):
    # TODO: learn about window size to improve smoothing and avoid
    #  'If mode is 'interp', window_length must be less than or equal to the size of x.' error
    window_size = min(41, len(scores))
    if window_size % 2 == 0:
        window_size -= 1  # must be odd number
    polynomial_order = min(3, window_size-1)
    if polynomial_order < 0:
        return scores
    return savgol_filter(scores, window_size, polynomial_order)
