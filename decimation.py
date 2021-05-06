import sys
import startin

from heapq import heappush, heappop
from ast import literal_eval

TRIANGULATION_THRESHOLD = 0.2
PROCESSING_THRESHOLD = 5000


class Triangulation:
    def __init__(self):
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

        self.triangulation = startin.DT()
        self.triangulation.set_is_init(True)

        self.processing_id = 1
        self.processing_index = 1

        self.finalized = {}

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.triangulation.output_bbox(min_x, min_y, max_x, max_y)

    def add_vertex(self, x, y, z):
        # self.vertices[self.vertex_id] = [x, y, z]

        self.triangulation.insert_vertex(self.vertex_id, x, y, z)

        self.vertex_id += 1

    def calculate_delta(self, vertex_id):
        vertex = self.triangulation.get_point(vertex_id)

        self.triangulation.remove(vertex_id)
        end_value = self.triangulation.interpolate_tin_linear(vertex[0], vertex[1])

        self.triangulation.insert_one_pt(vertex[0], vertex[1], vertex[2], vertex_id)

        return abs(end_value - vertex[2])

    def simplify_triangulation(self, finalize=False):

        # total_vertices = self.triangulation.number_of_vertices()

        # print("Processing {} vertices!".format(total_vertices))

        heap = []

        # Only get stars that have not yet been written
        for vertex_id in self.triangulation.all_vertex_ids_written(False):
            # Not infinite vertex or vertex on CH or vertex previously removed
            if not self.triangulation.can_vertex_be_removed(vertex_id):
                continue

            heappush(heap, (self.calculate_delta(vertex_id), vertex_id))

        try:
            smallest_delta_vertex = heappop(heap)
        except IndexError:  # No items in heap; no vertices 'can_vertex_be_removed()'
            return

        remove_count = 0

        while smallest_delta_vertex:
            # Get latest delta for this point
            delta = self.calculate_delta(smallest_delta_vertex[1])

            # If delta is still below threshold, throw it out
            if delta < TRIANGULATION_THRESHOLD:
                # print("Removing {} with delta {}".format(val[1], delta))
                remove_count += 1
                self.triangulation.remove(smallest_delta_vertex[1])

            try:
                smallest_delta_vertex = heappop(heap)
            except IndexError:
                smallest_delta_vertex = None

        # self.triangulation.write_geojson_triangles("data\\after_simplification" + str(remove_count) + ".json")

        self.triangulation.write_stars_obj(finalize)

        # for vertex in self.triangulation.all_unwritten_vertices(finalize):
        #     if vertex[0] > 0:
        #         sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")
        #
        # for edge in self.triangulation.all_unwritten_triangles():
        #     sys.stdout.write("f " + str(edge[0]) + " " + str(edge[1]) + " " + str(edge[2]) + "\n")

        # print("Removed {} points in decimation process".format(remove_count))
        # self.triangulation.cleanup_complete_stars()

    def new_star(self, index, neighbors):
        # self.finalized[index] = (True, len(neighbors))
        if neighbors:
            self.triangulation.define_star(index, neighbors)

        if self.vertex_id / self.processing_id >= PROCESSING_THRESHOLD:
            self.simplify_triangulation()
            self.processing_id += 1
            self.processing_index += PROCESSING_THRESHOLD

    def delete_vertex(self, index):
        self.finalized[index] = True
        # del self.vertices[index]
        # self.triangulation.remove(index)


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
            # self._triangulation.delete_vertex(int(data[0]))
            self._triangulation.new_star(int(data[0]), literal_eval("".join(data[1:])))

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin:
        processor.process_line(stdin_line)

    # Finalize remaining points
    triangulation.simplify_triangulation(finalize=True)

