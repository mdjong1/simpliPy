import os
import sys
import time

import psutil
import startinpy

from heapq import heappop, heapify
from ast import literal_eval

TRIANGULATION_THRESHOLD = 0.2
PROCESSING_THRESHOLD = 100000

INTERVAL = 100


class Triangulation:
    def __init__(self):
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

        self.triangulation = startinpy.DT()
        self.triangulation.set_is_init(True)

        self.processing_id = 1
        self.processing_index = 1

        self.finalized = {}

        self.memory_log_file = open(os.path.join(os.getcwd(), "memlog_decimation.csv"), "a")

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.triangulation.output_bbox(min_x, min_y, max_x, max_y)

    def add_vertex(self, x, y, z):
        self.triangulation.insert_vertex(self.vertex_id, x, y, z)

        self.vertex_id += 1

    def calculate_delta(self, vertex_id):
        vertex = self.triangulation.get_point(vertex_id)

        self.triangulation.remove(vertex_id)
        end_value = self.triangulation.interpolate_tin_linear(vertex[0], vertex[1])

        self.triangulation.insert_one_pt(vertex[0], vertex[1], vertex[2], vertex_id)

        return abs(end_value - vertex[2])

    def simplify_triangulation(self, finalize=False):

        did_something = False

        self.memory_log_file.write("Main, " + str(round(time.time())) + ", " + str(psutil.Process(os.getpid()).memory_info().rss) + "\n")

        heap = []

        # Only get stars that have not yet been written
        for vertex_id in self.triangulation.all_vertex_ids_written(False):
            # Not infinite vertex or vertex on CH or vertex previously removed
            if not self.triangulation.can_vertex_be_removed(vertex_id):
                continue

            heap.append((self.calculate_delta(vertex_id), vertex_id))

        sys.stderr.write("Size of heap: {}\n".format(len(heap)))
        sys.stderr.flush()

        heapify(heap)

        remove_count = 0
        removes_this_loop = 0

        while heap:
            smallest_delta_vertex = heappop(heap)

            # Get latest delta for this point
            delta = smallest_delta_vertex[0]

            # If delta is still below threshold, throw it out
            if delta < TRIANGULATION_THRESHOLD:
                remove_count += 1
                removes_this_loop += 1
                self.triangulation.remove(smallest_delta_vertex[1])
                did_something = True
            else:
                break

            if removes_this_loop % INTERVAL == 0:
                sys.stderr.write("Recalculating heap\n")
                sys.stderr.flush()

                removes_this_loop = 0

                for vertex_id in range(len(heap)):
                    if self.triangulation.can_vertex_be_removed(vertex_id):
                        heap[vertex_id] = (self.calculate_delta(vertex_id), vertex_id)

                heapify(heap)

        if did_something:
            self.triangulation.write_stars_obj(finalize)

    def new_star(self, index, neighbors):
        if neighbors:
            self.triangulation.define_star(index, neighbors)

        if self.vertex_id / self.processing_id >= PROCESSING_THRESHOLD:
            self.simplify_triangulation()
            self.processing_id += 1
            self.processing_index += PROCESSING_THRESHOLD

    def delete_vertex(self, index):
        self.finalized[index] = True


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def simplify(self):
        self._triangulation.simplify_triangulation()

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            pass

        elif identifier == "b":
            # bbox
            self._triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))

        elif identifier == "v":
            # vertex
            self._triangulation.add_vertex(float(data[0]), float(data[1]), float(data[2]))

        elif identifier == "f":
            # face
            pass

        elif identifier == "x":
            # vertex finalizer
            self._triangulation.new_star(int(data[0]), literal_eval("".join(data[1:])))

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    start_time = time.time()

    for stdin_line in sys.stdin:
        processor.process_line(stdin_line)

    # Finalize remaining points
    triangulation.simplify_triangulation(finalize=True)

    triangulation.memory_log_file.write("Main, " + str(round(time.time())) + ", " + str(psutil.Process(os.getpid()).memory_info().rss) + "\n")

    triangulation.memory_log_file.flush()

    triangulation.memory_log_file.close()

    sys.stderr.write("duration: " + str(time.time() - start_time) + "\n")


