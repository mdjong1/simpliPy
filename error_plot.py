import math
import geojson

import numpy as np
import seaborn as sns

from matplotlib import pyplot as plt

# input_file = "4-12-21\\errors_crop_10_groundonly_refinement_clearcorners.json"
input_file = "H:\\LAZ\\errors_twotiles_rand7_clipped.json"

with open(input_file) as f:
    gj = geojson.load(f)

errors = []

for vertex_id in range(len(gj["features"])):
    error = abs(gj["features"][vertex_id]["properties"]["error"])
    errors.append(error if type(error) == float else 0)

errors = np.array(errors)

print("Number of vertices tested = {}".format(len(errors)))

print("Largest error = {}".format(np.max(errors)))

print("Std Deviation = {}".format(np.std(errors)))

# rmse = math.sqrt(np.sum(np.square(errors) / len(errors)))
rmse = math.sqrt(np.average(errors))
print("RMSE = {}".format(rmse))

bins = np.linspace(0, 8, 40)

plt.figure(figsize=(10, 6), dpi=150)
plt.xlim(0, 8)

y_min = 0.17272893278376
max_pow = 8

y_max = pow(10, max_pow)

plt.ylim(ymin=y_min, ymax=y_max)

y_ticks = [y_min, 1]

for i in range(1, max_pow):
    y_ticks.append(pow(10, i))

y_ticks.append(y_max)

print(y_ticks)

plt.title("Two Tiles - FCFS")

sns.histplot(errors, bins=bins, log_scale=(False, True))

# https://stackoverflow.com/questions/16180946/drawing-average-line-in-histogram-matplotlib
min_ylim, max_ylim = plt.ylim()

print(min_ylim)

plt.axvline(0.2, color='k', linestyle='dashed', linewidth=1)
plt.text(0.2, max_ylim * 1.2, 'Threshold: {:.2f}'.format(0.2))

plt.axvline(rmse, color='r', linestyle='dashed', linewidth=1)
plt.text(rmse * 1.2, max_ylim * 0.2, 'RMSE: {:.2f}'.format(rmse))

plt.axvline(errors.mean(), color='b', linestyle='dashed', linewidth=1)
plt.text(errors.mean() * 1.4, max_ylim * 0.5, 'Mean: {:.2f}'.format(np.mean(errors)))

plt.xlabel("Vertex z-error (m)")
plt.ylabel("Frequency")

plt.yticks(y_ticks)

plt.show()


