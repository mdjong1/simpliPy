import math

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

print("Number of vertices tested = {}".format(len(errors)))

rmse = math.sqrt(np.average(errors))
print("RMSE = {}".format(rmse))

bins = np.linspace(0, 8, 40)

plt.hist(errors, bins=bins, log=True)

# https://stackoverflow.com/questions/16180946/drawing-average-line-in-histogram-matplotlib
min_ylim, max_ylim = plt.ylim()

plt.axvline(0.2, color='k', linestyle='dashed', linewidth=1)
plt.text(0.2, max_ylim * 1.2, 'Threshold: {:.2f}'.format(0.2))

plt.axvline(rmse, color='r', linestyle='dashed', linewidth=1)
plt.text(rmse * 1.2, max_ylim * 0.3, 'RMSE: {:.2f}'.format(rmse))

plt.axvline(errors.mean(), color='b', linestyle='dashed', linewidth=1)
plt.text(errors.mean() * 1.4, max_ylim * 0.6, 'Mean: {:.2f}'.format(errors.mean()))

plt.xlabel("Vertex z-error (m)")
plt.ylabel("Frequency")

plt.show()


