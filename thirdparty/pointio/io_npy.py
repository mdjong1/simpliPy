# This file is part of pointio.

# pointio is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pointio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pointio.  If not, see <http://www.gnu.org/licenses/>.

# Copyright 2015 Ravi Peters

import os
import numpy as np
import igraph


def write_npy(directory, datadict, keys=None):
    if keys is None:
        keys = []

    if not os.path.exists(directory):
        os.makedirs(directory)

    for key, val in list(datadict.items()):
        if key == 'ma_segment_graph':
            if type(datadict[key]) is igraph.Graph:
                datadict[key].write_pickle(os.path.join(directory, key + '.pickle'))

        elif key in keys or len(keys) == 0:
            file_name = os.path.join(directory, key)
            np.save(file_name, val)


def read_npy(directory, keys=None):
    if keys is None:
        keys = []

    assert os.path.exists(directory)

    if len(keys) == 0:
        keys = inspect_npy(directory)

    datadict = {}
    for key in keys:
        file_name = os.path.join(directory, key + '.npy')
        if os.path.exists(file_name):
            print(file_name)
            datadict[key] = np.load(file_name)

    file_name = os.path.join(directory, 'ma_segment_graph.pickle')
    if os.path.exists(file_name):
        datadict['ma_segment_graph'] = igraph.read(file_name)

    return datadict


def inspect_npy(directory):
    from glob import glob
    directory = os.path.join(directory, '*.npy')
    return [os.path.split(f)[-1][:-4] for f in glob(directory)]
