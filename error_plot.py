import geojson

import numpy as np

from matplotlib import pyplot as plt

# input_file = "4-12-21\\errors_crop_10_groundonly_refinement_clearcorners.json"
input_file = "H:\\LAZ\\errors_fourtiles_clipped.json"

with open(input_file) as f:
    gj = geojson.load(f)

errors = []

for vertex_id in range(len(gj["features"])):
    error = gj["features"][vertex_id]["properties"]["error"]
    errors.append(error if type(error) == float else 0)

errors = np.array(errors)

bins = np.linspace(0, 10, 44)

plt.hist(errors, bins=bins, log=True)

plt.xlabel("Vertex z-error (m)")
plt.ylabel("Frequency")

plt.show()

