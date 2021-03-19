import sys
import startin

import numpy as np

from heapq import heappop, heapify, _siftup, _siftdown
from math import floor

from scipy.spatial import KDTree

TRIANGULATION_THRESHOLD = 0.2


def is_almost(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)



class Triangulation:
    def __init__(self):
        self.total_points = None

        self.cell_size = None

        self.grid_dimensions = None
        self.grid_points = None
        self.triangulations = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}

        self.heap = None
        self.triangulation = None

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)
        self.triangulations = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point_in_grid(self, x, y, z):
        grid_cell = self.get_cell(x, y)

        if type(self.grid_points[grid_cell[0]][grid_cell[1]]) == list:
            self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
        else:
            self.grid_points[grid_cell[0]][grid_cell[1]] = [[x, y, z]]

        # # Always include points on outer bbox
        # if is_almost(x, self.min_x, abs_tol=0.0001) or is_almost(x, self.max_x, abs_tol=0.001) or \
        #         is_almost(y, self.min_y, abs_tol=0.001) or is_almost(y, self.max_y, abs_tol=0.001):
        #
        #     self.insert_point(x, y, z, grid_cell)
        #
        # else:
        #     interpolated_value = self.triangulations[grid_cell[0]][grid_cell[1]].interpolate_tin_linear(x, y)
        #
        #     if abs(interpolated_value - z) > TRIANGULATION_THRESHOLD:
        #         sys.stderr.write("{} - {} = {}\n".format(interpolated_value, z, abs(interpolated_value - z)))
        #         self.insert_point(x, y, z, grid_cell)

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def get_newest_max_abs(self, attempts=0):
        if attempts > 100:
            return heappop(self.heap)

        try:
            new_val = abs(self.triangulation.interpolate_tin_linear(self.heap[0][1][0], self.heap[0][1][1]) - self.heap[0][1][2]) * -1
        except OSError:
            return heappop(self.heap)

        old_val = self.heap[0]
        self.heap[0] = (new_val, self.heap[0][1])

        if new_val > old_val[0]:
            _siftup(self.heap, 0)
        else:
            _siftdown(self.heap, 0, 0)

        # Check if largest abs is still the same point
        if self.heap[0][1] != old_val[1]:
            return self.get_newest_max_abs(attempts=attempts + 1)

        try:
            return heappop(self.heap)
        except IndexError:
            return 0

    def finalize(self, grid_x, grid_y):

        self.heap = []

        self.triangulation = startin.DT()

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

        self.triangulation.insert(near_corner_points)

        if self.grid_points[grid_x][grid_y] is not None:
            for point in self.grid_points[grid_x][grid_y]:

                interpolated_value = self.triangulation.interpolate_tin_linear(point[0], point[1])

                # Heap is min-based, so multiply by -1 to ensure max delta is at top
                delta = abs(interpolated_value - point[2]) * -1

                self.heap.append((delta, point))

        heapify(self.heap)

        while True:

            largest_delta = self.get_newest_max_abs()

            if largest_delta[0] * -1 > TRIANGULATION_THRESHOLD:
                self.triangulation.insert_one_pt(largest_delta[1][0], largest_delta[1][1], largest_delta[1][2], 0)
            else:
                break

            # Recalculate all in heap
            # for i in range(len(self.heap)):
            #     new_val = self.triangulation.interpolate_tin_linear(self.heap[i][1][0], self.heap[i][1][1]) * -1
            #
            #     old_val = self.heap[i]
            #     self.heap[i] = (new_val, self.heap[i][1])
            #
            #     if new_val > old_val[0]:
            #         _siftup(self.heap, i)
            #     else:
            #         _siftdown(self.heap, 0, i)

            # try:
            #     interpolated_value = triangulation.interpolate_tin_linear(largest_delta[1][0], largest_delta[1][1])
            #
            #     if interpolated_value > TRIANGULATION_THRESHOLD:
            #         triangulation.insert_one_pt(largest_delta[1][0], largest_delta[1][1], largest_delta[1][2], 0)
            #
            # except OSError:
            #     pass
            #     # sys.stdout.write("Managed to find one outside CH\n")
            #     # triangulation.insert_one_pt(largest_delta[1][0], largest_delta[1][1], largest_delta[1][2], 0)


        for vertex in self.triangulation.all_vertices():
            if vertex[0] > 0:  # Exclude infinite vertex
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        self.triangulations[grid_x][grid_y] = None
        self.grid_points[grid_x][grid_y] = None


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
            self._triangulation.finalize(int(data[0]), int(data[1]))
            sys.stdout.write(input_line)

            # threading.Thread(target=self._triangulation.finalize, args=(int(data[0]), int(data[1]), input_line,)).start()

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)
