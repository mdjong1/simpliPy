# Decimation

!! Requires a [custom build](https://github.com/mdjong1/startinpy/tree/feature/insert_stars_directly) of startinPy
that allows direct insertion of vertices and stars.

# FCFS + Decim Refinement

Combines FCFS with Decimation

# FCFS Refinement

Refines streamed mesh based on which vertex is first encountered

# Garland-Heckbert Refinement

Refinement using only vertices which are affected by an insertion based on

```
@article{Garland1997,
abstract = {We present efficient algorithms for approximating a height field using a piecewise-linear triangulated surface. The algorithms attempt to minimize both the error and the number of triangles in the approximation. The methods we examine are variants of the greedy insertion algorithm. ...},
author = {Garland, Michael and Heckbert, P.S.},
journal = {Submitted for publication},
keywords = {data,data-dependent triangula-,delaunay triangulation,greedy insertion,our primary motivation is,surface approxima-,surface simplification,tion,to render height field,triangulated irregular network},
number = {October 1999},
pages = {1--19},
title = {{Fast triangular approximation of terrains and height fields}},
url = {http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.27.2086&rep=rep1&type=pdf},
year = {1997}
}

```

# Greedy Refinement

Refinement using an incremental recalculation interval

# MAT Simplification

Simplification using MASB and MAT by [Ravi Peters](https://github.com/tudelft3d/masbcpp/tree/kdtree2)

# Randomized Thinning

Randomized thinning based on 1/N points (average)

# Refinement

Basic refinement without incremental recalculation interval
