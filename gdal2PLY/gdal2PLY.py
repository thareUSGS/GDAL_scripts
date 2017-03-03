#!/usr/bin/python
# ########################################################################
# script originally posted to gis-stackexchange by Jake
# http://gis.stackexchange.com/questions/121561/generating-a-mesh-from-dtm
# Jake: http://gis.stackexchange.com/users/1931/jake
# original name: gdal_ratertotrn.py
# date posted on stackexchange: Nov 12 2014
#
# Note: does not currently hande NoDATA
#
# NoData work-around using GDAL
# 1.) find minimum Z value
# > gdalinfo -mm in_DEM.tif
# let's say min = -2790.594
# 2.) map GDAL Nodata to next round value down = -2791.
#   -- if DEM is large resample also. Example below resamples to 10 m/p
# > gdalwarp -dstnodata -2791 -tr 10 10 -r bilinear in_DEM.tif in_DEM_10m_nodata.tif
# 3.) now run this program in Python. I recommend Anaconda. Once installed type "conda instal gdal".
# > python gdal2PLY.py in_DEM_10m_nodata.tif out_DEM_10m.ply
#
# contact: Trent Hare, thare@usgs.gov
#

import sys
import numpy as np
from osgeo import gdal

def write_ply(filename, coordinates, triangles, binary=True):
    template = "ply\n"
    if binary:
        template += "format binary_" + sys.byteorder + "_endian 1.0\n"
    else:
        template += "format ascii 1.0\n"
    template += """element vertex {nvertices:n}
property float x
property float y
property float z
element face {nfaces:n}
property list int int vertex_index
end_header
"""

    context = {
     "nvertices": len(coordinates),
     "nfaces": len(triangles)
    }

    if binary:
        with  open(filename,'wb') as outfile:
            outfile.write(template.format(**context))
            coordinates = np.array(coordinates, dtype="float32")
            coordinates.tofile(outfile)

            triangles = np.hstack((np.ones([len(triangles),1], dtype="int") * 3,
                triangles))
            triangles = np.array(triangles, dtype="int32")
            triangles.tofile(outfile)
    else:
        with  open(filename,'w') as outfile:
            outfile.write(template.format(**context))
            np.savetxt(outfile, coordinates, fmt="%.3f")
            np.savetxt(outfile, triangles, fmt="3 %i %i %i")

def readraster(filename):
    raster = gdal.Open(filename)
    return raster


def createvertexarray(raster):
    transform = raster.GetGeoTransform()
    width = raster.RasterXSize
    height = raster.RasterYSize
    x = np.arange(0, width) * transform[1] + transform[0]
    y = np.arange(0, height) * transform[5] + transform[3]
    xx, yy = np.meshgrid(x, y)
    zz = raster.ReadAsArray()
    vertices = np.vstack((xx,yy,zz)).reshape([3, -1]).transpose()
    return vertices


def createindexarray(raster):
    width = raster.RasterXSize
    height = raster.RasterYSize

    ai = np.arange(0, width - 1)
    aj = np.arange(0, height - 1)
    aii, ajj = np.meshgrid(ai, aj)
    a = aii + ajj * width
    a = a.flatten()

    tria = np.vstack((a, a + width, a + width + 1, a, a + width + 1, a + 1))
    tria = np.transpose(tria).reshape([-1, 3])
    return tria


def main(argv):
    inputfile = argv[0]
    outputfile = argv[1]

    raster = readraster(inputfile)
    vertices = createvertexarray(raster)
    triangles = createindexarray(raster)

    write_ply(outputfile, vertices, triangles, binary=True)

if __name__ == "__main__":
    main(sys.argv[1:])