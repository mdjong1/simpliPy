import subprocess
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

    def set_bbox(self, min_x, min_y, max_x, max_y, min_z, max_z):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.min_z = min_z
        self.max_z = max_z

    def finalize(self, input_line, vertices, lock, memory_usage_queue):
        stdout_lines = []

        if len(vertices) > 0:

            for i in reversed(range(len(vertices))):
                if self.max_x < vertices[i][0] < self.min_x:
                    del vertices[i]
                elif self.max_y < vertices[i][1] < self.min_y:
                    del vertices[i]

            input_data = "b {} {} {} {} {} {}\n".format(self.min_x, self.min_y, self.max_x, self.max_y, self.min_z, self.max_z)

            input_data += "".join(["v {} {} {}\n".format(vertex[0], vertex[1], vertex[2]) for vertex in vertices])

            process = subprocess.Popen(
                ["thirdparty\\masbcpp\\mat_with_mediator_required.exe"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            shit = process.communicate(input_data)[0]

            stdout_lines.append(shit)

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

        self.vertices = []

        self.last_log_time = round(time.time())

        self.stdout_lock = Lock()
        self.memory_usage_queue = Queue()

        self.memory_usage_queue.put(MemoryUsage("Main", self.last_log_time, psutil.Process(os.getpid()).memory_info().rss))

        # self.memory_log_file = open(os.path.join(os.getcwd(), "memlog_refinement.csv"), "a")

        self.memory_usage_writer = Process(target=self.write_memory_usage, args=(self.memory_usage_queue,), daemon=True)
        self.memory_usage_writer.start()

    def write_memory_usage(self, memory_usage_queue):
        with open(os.path.join(os.getcwd(), "memlog_refinement.csv"), "a") as memory_log_file:
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
            self.triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]), float(data[4]), float(data[5]))
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            # All sprinkle points get passed to output directly
            if not self.sprinkling:
                self.vertices.append([float(data[0]), float(data[1]), float(data[2])])

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
            while len(self.processes) >= 1:
                for i in reversed(range(len(self.processes))):
                    if not self.processes[i].is_alive():
                        del self.processes[i]

                time.sleep(sleep_time)

            process = Process(target=self.triangulation.finalize, args=(input_line, self.vertices, self.stdout_lock, self.memory_usage_queue,), daemon=True)
            self.vertices = []
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
