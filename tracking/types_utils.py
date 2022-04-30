
# Deprecated
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
