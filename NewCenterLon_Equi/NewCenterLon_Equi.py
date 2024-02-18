#!/usr/bin/env python
###############################################################################
# $Id$
#
# Project:  GDAL Python scripts for LMMP (Lunar Mapping and Modeling Proj)
# Purpose: Set new center longitude without reprojecting the image,
#          just change registration. This should only be used for
#          projectons like Simple Cyl, Equirectangular, (maybe Mercator)
# Author: Trent Hare (USGS), Jan 2011
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
#If missing args, print usage and exit
def Usage():
    print('')
    print('Set new center longitude (central meridian) without resampling')
    print('')
    print('Usage: NewCenterLon_Equi.py [-of format] [-clon newClon] infile outfile')
    print('')
    sys.exit( 1 )

# =============================================================================
# convert string to GDAL Type enumeration
def ParseType(type):
    if (type == 'Byte'):
        return GDT_Byte
    elif (type == 'Int16'):
        return GDT_Int16
    elif (type == 'UInt16'):
        return GDT_UInt16
    elif (type == 'Int32'):
        return GDT_Int32
    elif (type == 'UInt32'):
        return GDT_UInt32
    elif (type == 'Float32'):
        return GDT_Float32
    elif (type == 'Float64'):
        return GDT_Float64
    elif (type == 'CInt16'):
        return GDT_CInt16
    elif (type == 'CInt32'):
        return GDT_CInt32
    elif (type == 'CFloat32'):
        return GDT_CFloat32
    elif (type == 'CFloat64'):
        return GDT_CFloat64
    else:
        return GDT_Byte
# =============================================================================

#set None for commandline options
newClon = None
infile = None
outfile = None
format = None

# =============================================================================
# Parse command line arguments.
# =============================================================================
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]

    if arg == '-of':
        i = i + 1
        format = sys.argv[i]
    elif arg == '-clon':
        i = i + 1
        newClon = float(sys.argv[i])
    elif infile is None:
        infile = arg
    elif outfile is None:
        outfile = arg
    else:
        Usage()
    i = i + 1

if newClon is None:
    newClon = 0
if format is None:
    format = 'GTiff'
if infile is None:
    Usage()
if outfile is None:
    Usage()

# Ensure we recognise the driver.
out_driver = gdal.GetDriverByName(format)
if out_driver is None:
    print ('"%s" driver not registered.' % format)
    sys.exit(1)
    
# Open input dataset
indataset = gdal.Open( infile, GA_ReadOnly )

# Read geotransform matrix and calculate ground coordinates
geomatrix = indataset.GetGeoTransform()
X = geomatrix[0] 
Y = geomatrix[3] 

# Build Spatial Reference object based on coordinate system, fetched from the
# opened dataset
srs = osr.SpatialReference()
srs.ImportFromWkt(indataset.GetProjection())

#Return Upper left X,Y in long,lat
srsLatLong = srs.CloneGeogCS()
ct = osr.CoordinateTransformation(srs, srsLatLong)
(long, lat, height) = ct.TransformPoint(X, Y)

#Set new center longitude
newSRS = srs
newSRS.SetProjParm("central_meridian",newClon)

#Return Upper left X,Y using new projection
ct = osr.CoordinateTransformation(srsLatLong, newSRS)
(X2, Y2, height) = ct.TransformPoint(long, lat)

#create new affine tuple
newGeomatrix = (X2, geomatrix[1], geomatrix[2], geomatrix[3], geomatrix[4], geomatrix[5])

# Report results
print('To Center Lon: %f' % (newClon))
print('Original X: %f\tShifted X: %f' % (X, X2))

#Get the raster type - Byte, Uint16, Float32, ...
aBand = indataset.GetRasterBand(1)
type = gdal.GetDataTypeName(aBand.DataType)
newType = ParseType(type)

#create copy of image and set new projection and registration
#outdataset = out_driver.Create(outfile, indataset.RasterXSize, indataset.RasterYSize, indataset.RasterCount, newType)
outdataset = out_driver.CreateCopy(outfile, indataset)
outdataset.SetProjection(newSRS.ExportToWkt())
outdataset.SetGeoTransform(newGeomatrix)

#simple loop for copying image in to image out - there is probably better method
#The better way was to us "CreateCopy" above
#loop over bands
#for iBand in range(1, indataset.RasterCount + 1):
    #inband = indataset.GetRasterBand(iBand)
    #outband = outdataset.GetRasterBand(iBand)

    #loop over lines
    #for i in range(inband.YSize - 1, -1, -1):
        #scanline = inband.ReadAsArray(0, i, inband.XSize, 1, inband.XSize, 1)
        #outband.WriteArray(scanline, 0, i)

    #update progress line
    #gdal.TermProgress( 1.0 - (float(i) / inband.YSize) )
        
