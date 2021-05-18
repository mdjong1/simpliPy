import random
import subprocess

import startin

from math import floor
from geojson import Point, Feature, FeatureCollection, dump

simplified_dt = "H:\\LAZ\\twotiles_rand7_clipped.obj"

original_laz = "H:\\LAZ\\twotiles_clipped.laz"

output_file = "H:\\LAZ\\errors_twotiles_rand7_clipped.json"

# interpolate 1/THINNING points
THINNING = 10


# Load simplified DT into Startin ✔
simplified_triangulation = startin.DT()

print("Starting error calculation process")

for line in open(simplified_dt, "r"):
    split_line = line.split(" ")
    identifier = split_line[0]
    data = split_line[1:]

    if identifier == "v":
        simplified_triangulation.insert_one_pt(float(data[0]), float(data[1]), float(data[2]))

print("Loaded up all {} of the vertices from the simplified DT".format(simplified_triangulation.number_of_vertices()))

# Load vertices from original DT as list ✔
original_vertices = []

las2txt = subprocess.Popen(["thirdparty\\lastools\\las2txt", "-i", original_laz, "-stdout"], stdout=subprocess.PIPE)

# For each vertex in the original DT ✔
    # Interpolate the error for this vertex ✔
    # Attach error for vertex to vertex class ✔

# https://gis.stackexchange.com/questions/130963/write-geojson-into-a-geojson-file-with-python

features = []

for line in las2txt.stdout:
    if random.randint(0, THINNING) == floor(THINNING / 2):
        stripped_line = str(line.rstrip(), "utf-8")
        split_line = stripped_line.split()
        split_line = [float(val) for val in split_line]

        x = split_line[0]
        y = split_line[1]
        z = split_line[2]

        try:
            interpolated_value = simplified_triangulation.interpolate_tin_linear(x, y)

            features.append(Feature(geometry=Point((x, y, z)), properties={"error": z - interpolated_value}))

        except OSError:
            print("Could not interpolate {}, {}".format(x, y))

print("Creating feature collection")

# Output each vertex to a GeoJSON file including attribute error ✔
feature_collection = FeatureCollection(features)

print("Writing to file")

with open(output_file, "w") as f:
    dump(feature_collection, f)
