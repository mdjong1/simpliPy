import math
import os
import subprocess
import time

from laspy.file import File
from numpy.ma import masked_array

from thirdparty.pointio import io_las, io_npy


class Bbox:
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def delta_x(self):
        return self.max_x - self.min_x

    def delta_y(self):
        return self.max_y - self.min_y


cell_size = 50
simplify_epsilon = 0.2

input_file = "H:\\LAZ\\c_37en1_big_delft.laz"
output_directory = "sliced"
npy_directory = "npyd"

loaded_file = File(input_file, mode="r")

bbox = Bbox(
    min_x=loaded_file.header.min[0],
    min_y=loaded_file.header.min[1],
    max_x=loaded_file.header.max[0],
    max_y=loaded_file.header.max[1]
)

width = bbox.delta_x() / cell_size
height = bbox.delta_y() / cell_size

max_dimension = width if width > height else height

cell_count = pow(2, math.ceil(math.log(max_dimension, 2)))

print("{0}x{1}, {2}".format(cell_count, cell_count, cell_size))

# Split to tiles of cell_size x cell_size with lastile
subprocess.run(["thirdparty\\lastools\\lastile", "-i", input_file, "-tile_size", str(cell_size), "-o", output_directory + "\\" + input_file.split("\\")[1]])

for file in os.listdir(output_directory):
    print(output_directory + "\\" + file)

    datadict = io_las.read_las(output_directory + "\\" + file)
    io_npy.write_npy(npy_directory + "\\" + file.split(".")[0], datadict, ['coords', 'offset'])

    time.sleep(1)


for subdirectory in os.listdir(npy_directory):
    subprocess.run(["thirdparty\\masbcpp\\compute_normals", npy_directory + "\\" + subdirectory])
    subprocess.run(["thirdparty\\masbcpp\\compute_ma", npy_directory + "\\" + subdirectory])
    subprocess.run(["thirdparty\\masbcpp\\simplify", "-i", "-e", str(simplify_epsilon), npy_directory + "\\" + subdirectory])

    datadict = io_npy.read_npy(npy_directory + "\\" + subdirectory)
    io_las.write_las("simplified" + "\\" + subdirectory + ".laz", datadict, datadict['decimate_lfs'])

    outfile = open("simplified" + "\\" + subdirectory + ".obj", mode="w")
    sstfin = subprocess.Popen(["thirdparty\\sst\\sstfin.exe", "simplified" + "\\" + subdirectory + ".laz", "10"], stdout=subprocess.PIPE)
    output = subprocess.Popen(["thirdparty\\sst\\sstdt.exe"], stdin=sstfin.stdout, stdout=outfile)

    time.sleep(1)

