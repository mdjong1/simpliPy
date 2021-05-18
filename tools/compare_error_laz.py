import sys
import random
import subprocess

import startin

from math import floor
from geojson import Point, Feature, FeatureCollection, dump

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) != 5:
        print("Invalid number of arguments used!")
        print("Usage: compare_error.py <original LAZ> <simplified TIN OBJ file> <output GeoJSON file> <thinning factor>")
        sys.exit()

    input_laz = sys.argv[1]
    input_simplified_tin = sys.argv[2]
    output_file = sys.argv[3]
    thinning_factor = int(sys.argv[4])

    # Load simplified DT into Startin ✔
    simplified_triangulation = startin.DT()

    print("Starting error calculation process")

    for line in open(input_simplified_tin, "r"):
        split_line = line.split(" ")
        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "v":
            simplified_triangulation.insert_one_pt(float(data[0]), float(data[1]), float(data[2]))

    print("Loaded up all {} of the vertices from the simplified DT".format(simplified_triangulation.number_of_vertices()))

    # Load vertices from original DT as list ✔
    original_vertices = []

    las2txt = subprocess.Popen(["thirdparty\\lastools\\las2txt", "-i", input_laz, "-stdout"], stdout=subprocess.PIPE)

    # https://gis.stackexchange.com/questions/130963/write-geojson-into-a-geojson-file-with-python
    features = []

    # For each vertex in the original DT ✔
    for line in las2txt.stdout:
        if random.randint(0, thinning_factor) == floor(thinning_factor / 2):
            stripped_line = str(line.rstrip(), "utf-8")
            split_line = stripped_line.split()
            split_line = [float(val) for val in split_line]

            x = split_line[0]
            y = split_line[1]
            z = split_line[2]

            try:
                # Interpolate the error for this vertex ✔
                interpolated_value = simplified_triangulation.interpolate_tin_linear(x, y)

                # Attach error for vertex to vertex class ✔
                features.append(Feature(geometry=Point((x, y, z)), properties={"error": z - interpolated_value}))

            except OSError:
                print("Could not interpolate {}, {}; skipping.".format(x, y))

    print("Creating feature collection")

    # Output each vertex to a GeoJSON file including attribute error ✔
    feature_collection = FeatureCollection(features)

    print("Writing to file")

    with open(output_file, "w") as f:
        dump(feature_collection, f)
