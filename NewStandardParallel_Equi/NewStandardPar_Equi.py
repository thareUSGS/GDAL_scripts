#!/usr/bin/env python
###############################################################################
# $Id$
#
# Project:  GDAL Python scripts for LMMP (Lunar Mapping and Modeling Proj)
# Purpose: Set new standard_parallel_1 without reprojecting the image,
#          just change registration. This should only be used for
#          projections like Equirectangular. This can result in rectangular 
#          pixels.
# Author: Trent Hare (USGS), Apr. 2023
# Based on tolatlong by Andrey Kiselev, dron@remotesensing.org
#
###############################################################################
# Copyright (c) 2003, Andrey Kiselev <dron@remotesensing.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo.gdalconst import *

    gdal.TermProgress = gdal.TermProgress_nocb
    gdal.DontUseExceptions()
except ImportError:
    import gdal
    from gdalconst import *

import sys
import string


# =============================================================================
# If missing args, print usage and exit
def Usage():
    print("")
    print("Set new standard_parallel_1 (latitude of true scale) without resampling")
    print("")
    print("Usage: NewStandardPar_Equi.py [-of format] [-clat newClat] infile outfile")
    print("")
    sys.exit(1)


# =============================================================================
# convert string to GDAL Type enumeration
def ParseType(type):
    if type == "Byte":
        return GDT_Byte
    elif type == "Int16":
        return GDT_Int16
    elif type == "UInt16":
        return GDT_UInt16
    elif type == "Int32":
        return GDT_Int32
    elif type == "UInt32":
        return GDT_UInt32
    elif type == "Float32":
        return GDT_Float32
    elif type == "Float64":
        return GDT_Float64
    elif type == "CInt16":
        return GDT_CInt16
    elif type == "CInt32":
        return GDT_CInt32
    elif type == "CFloat32":
        return GDT_CFloat32
    elif type == "CFloat64":
        return GDT_CFloat64
    else:
        return GDT_Byte


# =============================================================================

# set None for commandline options
newClat = None
infile = None
outfile = None
format = None

# =============================================================================
# Parse command line arguments.
# =============================================================================
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]

    if arg == "-of":
        i = i + 1
        format = sys.argv[i]
    elif arg == "-clat":
        i = i + 1
        newClat = float(sys.argv[i])
    elif infile is None:
        infile = arg
    elif outfile is None:
        outfile = arg
    else:
        Usage()
    i = i + 1

if newClat is None:
    newClat = 0
if format is None:
    format = "GTiff"
if infile is None:
    Usage()
if outfile is None:
    Usage()

# Ensure we recognize the driver.
out_driver = gdal.GetDriverByName(format)
if out_driver is None:
    print('"%s" driver not registered.' % format)
    sys.exit(1)

# Open input dataset
indataset = gdal.Open(infile, GA_ReadOnly)

# Read geotransform matrix and calculate ground coordinates
geomatrix = indataset.GetGeoTransform()
maxy = geomatrix[3]
cellsizey = geomatrix[5]
minx = geomatrix[0]
cellsizex = geomatrix[1]
maxx = minx + (cellsizex * indataset.RasterXSize)
extentx = maxx - minx

# Build Spatial Reference object based on coordinate system, fetched from the
# opened dataset
srs = osr.SpatialReference()
srs.ImportFromWkt(indataset.GetProjection())

srsLatLong = srs.CloneGeogCS()
ct = osr.CoordinateTransformation(srs, srsLatLong)
# Return Upper left X,Y in long,lat
(long1, lat1, height1) = ct.TransformPoint(minx, maxy)
# Return Upper right X,Y in long,lat
(long2, lat2, height2) = ct.TransformPoint(maxx, maxy)

# Set new std_par_1
newSRS = srs
newSRS.SetProjParm("standard_parallel_1", newClat)

# Return Upper left X,Y using new projection
ct = osr.CoordinateTransformation(srsLatLong, newSRS)
(newminx, newmaxy, height) = ct.TransformPoint(long1, lat1)
# Return Upper right X,Y using new projection
(newmaxx, newmaxy, height) = ct.TransformPoint(long2, lat2)
newextentx = newmaxx - newminx
newcellsizex = newextentx / indataset.RasterXSize


# create new affine tuple
newGeomatrix = (
    newminx,
    newcellsizex,
    geomatrix[2],
    geomatrix[3],
    geomatrix[4],
    geomatrix[5],
)

# Report results
print("To standard_parallel_1: %f" % (newClat))
print("Original X: %f\tShifted X: %f" % (minx, newminx))
print("Original Y cellsize (will be unchanged): %f" % (-cellsizey))
print("Original X cellsize: %f\tNew X cellsize: %f" % (cellsizex, newcellsizex))

# Get the raster type - Byte, Uint16, Float32, ...
aBand = indataset.GetRasterBand(1)
type = gdal.GetDataTypeName(aBand.DataType)
newType = ParseType(type)

# create copy of image and set new projection and registration
# outdataset = out_driver.Create(outfile, indataset.RasterXSize, indataset.RasterYSize, indataset.RasterCount, newType)
outdataset = out_driver.CreateCopy(outfile, indataset)
outdataset.SetProjection(newSRS.ExportToWkt())
outdataset.SetGeoTransform(newGeomatrix)
