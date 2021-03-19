import sys
from heapq import _siftup, _siftdown, _heappop_max

import startin

import numpy as np

from math import floor

from heapq import *

from scipy.spatial import KDTree

TRIANGULATION_THRESHOLD = 0.2

class Triangle:
    def __init__(self, vertices):
        self.vertices = vertices
        self.points = {}


class Triangulation:
    def __init__(self):
        self.total_points = None

        self.cell_size = None

        self.grid_dimensions = None
        self.grid_points = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.heap = []

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point_in_grid(self, x, y, z):
        grid_cell = self.get_cell(x, y)

        if type(self.grid_points[grid_cell[0]][grid_cell[1]]) == list:
            self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
        else:
            self.grid_points[grid_cell[0]][grid_cell[1]] = [[x, y, z]]

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def get_corner_points(self, grid_x, grid_y):
        x_vals = []
        y_vals = []

        for point in self.grid_points[grid_x][grid_y]:
            x_vals.append(point[0])
            y_vals.append(point[1])

        tree = KDTree(np.c_[x_vals, y_vals])

        corner_points = [
            [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y)],
            [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y)],
            [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5],
            [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5]
        ]

        near_corner_points = []

        for corner_point in corner_points:
            # Get nearest point to corner
            distances, indexes = tree.query(corner_point, k=10)

            z_vals = [self.grid_points[grid_x][grid_y][index][2] for index in indexes]

            # add a corner point with average z value of 10 nearest
            near_corner_points.append([corner_point[0], corner_point[1], sum(z_vals) / len(z_vals)])

        return near_corner_points

    def heap_update(self, max_error, index, triangle):
        old_val = self.heap[index]
        self.heap[index] = (max_error, self.heap[index][1], triangle)

        if max_error > old_val[0]:
            _siftup(self.heap, index)
        else:
            _siftdown(self.heap, 0, index)

    def heap_change(self, max_error, index, triangle):

        if index <= len(self.heap):
            self.heap_update(max_error * -1, index, triangle)
        else:
            heappush(self.heap, (max_error * -1, index, triangle))

    def initial_scan_triangle(self, triangulation, triangle, all_points):
        best = None
        max_error = 0

        output_triangle = Triangle(triangle)

        for i in range(len(all_points)):
            point = all_points[i]

            # TODO: Remember in which triangle a point is and keep that knowledge; only update if it is in a split triangle
            in_triangle = triangulation.locate(point[0], point[1])

            is_inside_triangle = all(item in triangle for item in in_triangle)

            if is_inside_triangle:

                output_triangle.points[i] = point

                error = abs(point[2] - triangulation.interpolate_tin_linear(point[0], point[1]))

                if error > max_error:
                    max_error = error
                    best = i

        if best is not None:
            self.heap_change(max_error, best, output_triangle)

    def scan_triangle(self, triangulation, input_triangle):
        best = None
        max_error = 0

        output_triangle = Triangle(input_triangle.vertices)

        for i in input_triangle.points:
            point = input_triangle.points[i]

            in_triangle = triangulation.locate(point[0], point[1])

            is_inside_triangle = all(item in input_triangle.vertices for item in in_triangle)

            if is_inside_triangle:
                output_triangle.points[i] = point

                error = abs(point[2] - triangulation.interpolate_tin_linear(point[0], point[1]))

                if error > max_error:
                    max_error = error
                    best = i

        if best is not None:
            self.heap_change(max_error, best, output_triangle)

    def insert(self, triangulation, all_points, max_abs):
        index = max_abs[1]

        triangulation.insert_one_pt(all_points[index][0], all_points[index][1], all_points[index][2], 0)

        containing_triangle = triangulation.locate(all_points[index][0], all_points[index][1])

        adjacent_triangles = triangulation.adjacent_triangles_to_triangle(containing_triangle)

        # FIXME: Get triangle object for adjacents instead of triangle vertex pointers
        if adjacent_triangles is not None:
            for triangle in adjacent_triangles:
                self.scan_triangle(triangulation, triangle)

    def finalize(self, grid_x, grid_y, input_line):
        all_points = self.grid_points[grid_x][grid_y]

        if len(all_points) == 0:
            sys.stdout.write(input_line)
            return

        corner_points = self.get_corner_points(grid_x, grid_y)

        triangulation = startin.DT()

        # Insert 4 corner points into triangulation
        triangulation.insert(corner_points)

        for triangle in triangulation.all_triangles():
            self.initial_scan_triangle(triangulation, triangle, all_points)

        while True:
            max_abs = heappop(self.heap)

            print(max_abs)

            if max_abs[0] * -1 < TRIANGULATION_THRESHOLD:
                break

            self.insert(triangulation, all_points, max_abs)

        self.heap = []

        for vertex in triangulation.all_vertices():
            if vertex[0] > 0:
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        sys.stdout.write(input_line)


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            pass

        elif identifier == "n":
            # Total number of points
            self._triangulation.total_points = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            self._triangulation.initialize_grid(int(data[0]))
            sys.stdout.write(input_line)

        elif identifier == "s":
            # Cell size
            self._triangulation.cell_size = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "b":
            # bbox
            self._triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            self._triangulation.insert_point_in_grid(float(data[0]), float(data[1]), float(data[2]))

        elif identifier == "x":
            # cell finalizer
            self._triangulation.finalize(int(data[0]), int(data[1]), input_line)

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    tr = Triangulation()
    processor = Processor(tr)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)

