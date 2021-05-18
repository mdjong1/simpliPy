import sys
import random

import startin

from geojson import Point, Feature, FeatureCollection, dump

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) != 4:
        print("Invalid number of arguments used!")
        print("Usage: compare_error.py <full TIN OBJ file> <simplified TIN OBJ file> <output GeoJSON file>")
        sys.exit()

    input_full_tin = sys.argv[1]
    input_simplified_tin = sys.argv[2]
    output_file = sys.argv[3]

    # Load simplified DT into Startin ✔
    simplified_triangulation = startin.DT()

    for line in open(input_simplified_tin, "r"):
        split_line = line.split(" ")
        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "v":
            simplified_triangulation.insert_one_pt(float(data[0]), float(data[1]), float(data[2]), 0)

    # Load vertices from original DT as list ✔
    original_vertices = []

    for line in open(input_full_tin, "r"):
        split_line = line.split(" ")
        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "v":
            original_vertices.append([float(data[0]), float(data[1]), float(data[2])])

    # https://gis.stackexchange.com/questions/130963/write-geojson-into-a-geojson-file-with-python
    features = []

    last_percentage = -1

    # interpolate 1/10 points
    THINNING = 10

    print("Going to interpolate {} vertices!".format(len(original_vertices)))

    # For each vertex in the original DT ✔
    for i in range(len(original_vertices)):
        vertex = original_vertices[i]

        if i % 10000 == 0:
            percentage = round(i / len(original_vertices))
            print(percentage, "% done")
            if percentage != last_percentage:
                print(percentage, "% done")
                last_percentage = percentage

        if random.randint(0, THINNING) == THINNING / 2:
            try:
                # Interpolate the error for this vertex ✔
                interpolated_value = simplified_triangulation.interpolate_tin_linear(vertex[0], vertex[1])

                # Attach error for vertex to vertex class ✔
                features.append(Feature(geometry=Point((vertex[0], vertex[1], vertex[2])), properties={"error": abs(vertex[2] - interpolated_value)}))

            except OSError:
                print("Could not interpolate {}, {}; skipping.".format(vertex[0], vertex[1]))

    # Output each vertex to a GeoJSON file including attribute error ✔
    feature_collection = FeatureCollection(features)

    with open(output_file, "w") as f:
        dump(feature_collection, f)
