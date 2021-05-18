import sys

from geojson import Point, LineString, Feature, FeatureCollection, dump

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) != 3:
        print("Invalid number of arguments used!")
        print("Usage: objtogeojson.py <input OBJ file> <output GeoJSON file>")
        sys.exit()

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    vertices = []
    features = []

    for line in open(input_file, "r"):
        split_line = line.strip().split(" ")
        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "v":
            vertex = [float(val) for val in data]

            vertices.append(vertex)

            features.append(Feature(geometry=Point(tuple(vertex))))

        if identifier == "f":
            line = tuple([vertices[index - 1] for index in [int(val) for val in data]])
            features.append(Feature(geometry=LineString(line)))

    feature_collection = FeatureCollection(features)

    with open(output_file, 'w') as f:
        dump(feature_collection, f)
