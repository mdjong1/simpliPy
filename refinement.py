import queue
import sys
import threading

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
    #     self.stdout = queue.Queue()
    #
    #     threading.Thread(target=self.worker, daemon=True).start()
    #
    # def worker(self):
    #     while True:
    #         sys.stdout.write(self.stdout.get())
    #         sys.stdout.flush()
    #         self.stdout.task_done()

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

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def finalize(self, grid_x, grid_y, input_line):

        if self.grid_points[grid_x][grid_y] is None:
            sys.stdout.write(input_line)
            # self.stdout.put(input_line)
            return

        heap = []

        triangulation = startin.DT()

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

        triangulation.insert(near_corner_points)

        for point in self.grid_points[grid_x][grid_y]:

            interpolated_value = triangulation.interpolate_tin_linear(point[0], point[1])

            # Heap is min-based, so multiply by -1 to ensure max delta is at top
            delta = abs(interpolated_value - point[2]) * -1

            heap.append((delta, point))

        heapify(heap)

        while True:
            # sys.stdout.write("{}\n".format(len(heap)))

            try:
                largest_delta = heappop(heap)
            except IndexError:
                break

            try:
                if largest_delta[0] * -1 > TRIANGULATION_THRESHOLD:
                    triangulation.insert_one_pt(largest_delta[1][0], largest_delta[1][1], largest_delta[1][2], 0)
                else:
                    break

            except OSError:
                pass
                # sys.stdout.write("Managed to find one outside CH\n")
                # triangulation.insert_one_pt(largest_delta[1][0], largest_delta[1][1], largest_delta[1][2], 0)

            # For every 10 points; recalculate the entire heap's errors
            if len(heap) % 10 == 0:
                for i in range(len(heap)):
                    new_val = abs(triangulation.interpolate_tin_linear(heap[i][1][0], heap[i][1][1]) - heap[i][1][2]) * -1

                    old_val = heap[i]
                    heap[i] = (new_val, heap[i][1])

                    if new_val > old_val[0]:
                        _siftup(heap, i)
                    else:
                        _siftdown(heap, 0, i)

        for vertex in triangulation.all_vertices():
            if vertex[0] > 0:  # Exclude infinite vertex.
                # self.stdout.put("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        # self.stdout.put(input_line)
        sys.stdout.write(input_line)

        self.triangulations[grid_x][grid_y] = None
        self.grid_points[grid_x][grid_y] = None


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

        self.threads = []

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
            # self._triangulation.finalize(int(data[0]), int(data[1]), input_line)

            thread = threading.Thread(target=self._triangulation.finalize, args=(int(data[0]), int(data[1]), input_line,), daemon=True)
            self.threads.append(thread)
            thread.start()

        else:
            # Unknown identifier in stream
            pass

        sys.stdout.flush()


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)

    for thread in processor.threads:
        thread.join()
