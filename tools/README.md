# compare_error.py
`Usage: compare_error.py <full TIN OBJ file> <simplified TIN OBJ file> <output GeoJSON file>`

Compares error between a full TIN and a simplified TIN and stores the result in a GeoJSON containing
vertices and an error attribute.

# compare_error_laz.py
`Usage: compare_error.py <original LAZ> <simplified TIN OBJ file> <output GeoJSON file> <thinning factor>`

Compares error between a LAZ file and a simplified TIN and stored the result in a GeoJSON containing
vertices and an error attribute. Allows for setting a thinning factor if input LAZ is very large.

Note: If simplified TIN is created with only ground, water, and building classes, ensure LAZ is as well.

# error_plot.py
`Usage: set 3 parameters at top of file`

Define an input file created by one of the `compare_error` scripts, a threshold (so this can be drawn to
the plot), and define a title for the plot. Will return exact values for max error, std deviation, and RMSE
to the console output.

# geojsontoobj.py
[GeoJSON to OBJ](https://github.com/mdjong1/geojson-to-obj)

`Usage: geojsontoobj.py <input GeoJSON file> <output OBJ file>`

(Super basic) conversion of a GeoJSON file into an OBJ file

# gpkgtogeojson.py
[GPKG to GeoJSON](https://github.com/mdjong1/gpkg-to-geojson)

`Usage: gpkgtogeojson.py <input GPKG file> <output GeoJSON file>`

(Super basic) conversion of a GKPG file into an GeoJSON file

# objtogeojson.py
[OBJ to GeoJSON](https://github.com/mdjong1/Obj-to-GeoJSON)

`Usage: objtogeojson.py <input OBJ file> <output GeoJSON file>`

(Super basic) conversion of an OBJ file into an GeoJSON file

# streaming_clip_obj.py
`Usage: streaming_clip_obj.py <input OBJ file> <minX> <minY> <maxX> <maxY> > <output_file.obj>`

Allows OBJ files to be clipped while streaming. Specify your bounding box by setting minX, minY,
maxX, and maxY. Choose an input file and output OBJ containing only vertices within your bbox will be written to stdout.

# streaming_vertex_counter.py
`Usage: Set file path at top of file`

Outputs how many vertices and triangles (faces) are present in the chosen file.
