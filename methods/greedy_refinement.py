import sys
import os
import time
from math import floor

import psutil

import startin

import numpy as np

from heapq import heappop, heapify
from multiprocessing import cpu_count, Process, Queue, current_process, Lock
from scipy.spatial import KDTree

RECALCULATION_INTERVAL_STEP_SIZE = 1/2
RECALCULATION_INTERVAL_UPPER_BOUNDARY = 25

TRIANGULATION_THRESHOLD = 0.2
DELTA_PRECISION = 1E4


class MemoryUsage:
    def __init__(self, process_name, timestamp, memory_usage):
        self.process_name = process_name
        self.timestamp = timestamp
        self.memory_usage = memory_usage


class Vertex:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.delta_z = 0

    def __str__(self):
        return "{} {} {} - {}".format(self.x, self.y, self.z, (self.delta_z / DELTA_PRECISION) * -1)

    def __lt__(self, other):
        return self.delta_z < other.delta_z


class Triangulation:
    def __init__(self):
        self.cell_size = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def insert_vertex(self, x, y, z):
        self.vertices[self.vertex_id] = Vertex(x, y, z)
        self.vertex_id += 1

    def finalize(self, input_line, grid_x, grid_y, vertices, lock, memory_usage_queue):
        stdout_lines = []

        if len(vertices) > 0:

            last_log_time = round(time.time())
            memory_usage_queue.put(MemoryUsage(current_process().name, last_log_time, psutil.Process(os.getpid()).memory_info().rss))

            triangulation = startin.DT()

            x_vals = []
            y_vals = []
            z_vals = []

            for vertex_id, vertex in vertices.items():
                x_vals.append(vertex.x)
                y_vals.append(vertex.y)
                z_vals.append(vertex.z)

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

                queried_z_vals = [z_vals[index] for index in indexes if index < len(z_vals)]

                # add a corner point with average z value of 10 nearest
                near_corner_points.append([corner_point[0], corner_point[1], sum(queried_z_vals) / len(queried_z_vals)])

            triangulation.insert(near_corner_points)

            heap = []

            for vertex_id, vertex in vertices.items():
                try:
                    interpolated_value = triangulation.interpolate_tin_linear(vertex.x, vertex.y)

                    vertex.delta_z = round(abs(interpolated_value - vertex.z) * DELTA_PRECISION) * -1

                    heap.append(vertex)

                # If outside CH, always insert
                except OSError:
                    triangulation.insert_one_pt(vertex.x, vertex.y, vertex.z)

            heapify(heap)

            recalculation_interval = 5
            points_processed_this_loop = 0

            while heap:

                current_time = round(time.time())

                if current_time != last_log_time:
                    memory_usage_queue.put(MemoryUsage(current_process().name, current_time, psutil.Process(os.getpid()).memory_info().rss))
                    last_log_time = current_time

                largest_delta = heappop(heap)

                if (largest_delta.delta_z / DELTA_PRECISION) * -1 > TRIANGULATION_THRESHOLD:
                    try:
                        triangulation.insert_one_pt(largest_delta.x, largest_delta.y, largest_delta.z)
                        points_processed_this_loop += 1

                    # Somehow point is outside bbox, ignore
                    except OSError:
                        pass
                else:
                    break

                if points_processed_this_loop % floor(recalculation_interval) == 0:
                    points_processed_this_loop = 0
                    recalculation_interval += RECALCULATION_INTERVAL_STEP_SIZE

                    for i in range(len(heap)):
                        try:
                            interpolated_value = triangulation.interpolate_tin_linear(heap[i].x, heap[i].y)

                            # Heap is min-based, so multiply by -1 to ensure max delta is at top
                            heap[i].delta_z = round(abs(interpolated_value - heap[i].z) * DELTA_PRECISION) * -1

                        # Somehow outside CH; ignore
                        except OSError:
                            pass

                    heapify(heap)

            if triangulation.number_of_vertices() > 4:
                # Remove initial corners
                for i in [1, 2, 3, 4]:
                    triangulation.remove(i)

            # Output all remaining vertices
            for vertex in triangulation.all_vertices():
                if vertex[0] > 0:  # Exclude infinite vertex
                    stdout_lines.append("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        with lock:
            stdout_lines.append(input_line)
            sys.stdout.write("".join(stdout_lines))
            sys.stdout.flush()

        sys.stderr.write(current_process().name + " - FINISHED.\n")


class Processor:
    def __init__(self, dt):
        self.triangulation = dt

        self.sprinkling = True
        self.processes = []

        self.last_log_time = round(time.time())

        self.stdout_lock = Lock()
        self.memory_usage_queue = Queue()

        self.memory_usage_queue.put(MemoryUsage("Main", self.last_log_time, psutil.Process(os.getpid()).memory_info().rss))

        # self.memory_log_file = open(os.path.join(os.getcwd(), "memlog_refinement.csv"), "a")

        self.memory_usage_writer = Process(target=self.write_memory_usage, args=(self.memory_usage_queue,), daemon=True)
        self.memory_usage_writer.start()

    def write_memory_usage(self, memory_usage_queue):
        with open(os.path.join(os.getcwd(), "../memlog_refinement.csv"), "a") as memory_log_file:
            while True:
                val = memory_usage_queue.get()

                if val:
                    memory_log_file.write(str(val.process_name) + ", " + str(val.timestamp) + ", " + str(val.memory_usage) + "\n")
                    memory_log_file.flush()
                else:
                    time.sleep(0.5)

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        current_time = round(time.time())

        if current_time != self.last_log_time:
            self.memory_usage_queue.put(MemoryUsage("Main", current_time, psutil.Process(os.getpid()).memory_info().rss))
            self.last_log_time = current_time

        if identifier == "#" or identifier == "":
            if data[0] == "endsprinkle":
                self.sprinkling = False
                sys.stderr.write("Sprinkling done!\n")

        elif identifier == "n":
            # Total number of points
            self.triangulation.total_points = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            sys.stdout.write(input_line)

        elif identifier == "s":
            # Cell size
            self.triangulation.cell_size = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "b":
            # bbox
            self.triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            # All sprinkle points get passed to output directly
            if not self.sprinkling:
                self.triangulation.insert_vertex(float(data[0]), float(data[1]), float(data[2]))

            else:
                sys.stdout.write(input_line)

        elif identifier == "x":
            # cell finalizer
            # While sprinkling, don't bother processing since all finalized cells now are still empty anyways
            if self.sprinkling:
                sys.stdout.write(input_line)
                return

            sys.stderr.write("Starting new process to finalize cell: {}, {}. Processing currently running: {}\n".format(data[0], data[1], len(self.processes)))
            sys.stderr.flush()

            sleep_time = 1

            # Ensure total number of processes never exceeds capacity
            while len(self.processes) >= cpu_count() - 4:
                for i in reversed(range(len(self.processes))):
                    if not self.processes[i].is_alive():
                        del self.processes[i]

                time.sleep(sleep_time)

            process = Process(target=self.triangulation.finalize, args=(input_line, int(data[0]), int(data[1]), self.triangulation.vertices, self.stdout_lock, self.memory_usage_queue,), daemon=True)
            self.triangulation.vertices = {}
            self.triangulation.vertex_id = 1
            self.processes.append(process)
            process.start()

        else:
            # Unknown identifier in stream
            pass

        sys.stdout.flush()


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)
    start_time = time.time()

    for stdin_line in sys.stdin:
        processor.process_line(stdin_line)

    for process in processor.processes:
        process.join()

    # processor.memory_log_file.flush()
    #
    # processor.memory_log_file.close()

    processor.memory_usage_writer.terminate()

    sys.stderr.write("duration: " + str(time.time() - start_time) + "\n")
