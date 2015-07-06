#!/usr/bin/env python
#******************************************************************************
#  $Id$
#  Name:     gdal_clipper_prep.py 
#  Project:  GDAL Python Interface
#  Purpose:  Given a synthesized Europa Clipper (DEM) surface, users can flip,
#            apply scale and offset, parameters, map negatives to NoData and
#            interpolate over, pad image to the left or right.
#
#            Note: many parameters are hard-wired for our application
#
#  Author:   Trent Hare, thare@usgs.gov
#  Credits:  Based on python GDAL samples 
#            http://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/
# 
#******************************************************************************
#  Copyright (c) 2015, Trent Hare
# 
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#******************************************************************************

import math
import sys
import os
try:
   from osgeo import gdal
   from osgeo.gdalconst import *
   gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *

try:
    import numpy as np
except ImportError:
    import Numeric as np

#from scipy.ndimage import generic_filter

# =============================================================================
# Usage()
def Usage():
    print("""
Usage: gdal_clipper_update.py [-of ENVI] [-flip] [-positive] [-fill] [-scale] [-ot UInt16] [-padLeft] [-padRight] infile.fit outfile.tif

example:
gdal_clipper_prep.py -of ENVI -ot UInt16 -fill -positive -scale -padRight 02L_b_000003.fit 02L_b_000003_pad.raw
or
gdal_clipper_prep.py -ot UInt16 -fill -positive -scale -padRight 02L_b_000003.fit 02L_b_000003_pad.tif
""")
    sys.exit(1)

# =============================================================================
# convert string to GDAL Type enumeration
def ParseType(type):
    if type == 'Byte':
        return GDT_Byte
    elif type == 'Int16':
        return GDT_Int16
    elif type == 'UInt16':
        return GDT_UInt16
    elif type == 'Int32':
        return GDT_Int32
    elif type == 'UInt32':
        return GDT_UInt32
    elif type == 'Float32':
        return GDT_Float32
    elif type == 'Float64':
        return GDT_Float64
    elif type == 'CInt16':
        return GDT_CInt16
    elif type == 'CInt32':
        return GDT_CInt32
    elif type == 'CFloat32':
        return GDT_CFloat32
    elif type == 'CFloat64':
        return GDT_CFloat64
    else:
        return GDT_Byte

# set up some recommended default nodatavalues for each datatype
def ParseNoData(type):
    if type == 'Byte':
        return 0
    elif type == 'Int16':
        return -32768 
    elif type == 'UInt16':
        return 0
    elif type == 'Int32':
        return -2147483647
    elif type == 'UInt32':
        return 0
    elif type == 'Float32':
        return -3.402823466E+38
    elif type == 'Float64':
        return -1.7976931348623158E+308 
    else:
        return 0

# =============================================================================
# 	Mainline
# =============================================================================
argv = gdal.GeneralCmdLineProcessor( sys.argv )

infile = None
outfile = None
format = None
outType = None
outNoData = None
quiet = False
padLeft = False
padRight = False
padSize = 3664
scale = False
flip = False
fill = False
positive = False

# Parse command line arguments.
i = 1
while i < len(sys.argv):
    arg = argv[i]
    if arg == '-of':
        i = i + 1
        format = argv[i]
    elif arg == '-ot':
        i = i + 1
        outType = argv[i]
    elif arg == '-padLeft':
        padLeft = True
    elif arg == '-padRight':
        padRight = True
    elif arg == '-q' or arg == '-quiet':
        quiet = True
    elif arg == '-f' or arg == '-flip':
        flip = True
    elif arg == '-fill':
        fill = True
    elif arg == '-positive':
        positive = True
    elif arg == '-s' or arg == '-scale':
        scale = True
    elif infile is None:
        infile = arg
    elif outfile is None:
        outfile = arg
    else:
        Usage()
    i = i + 1

if format is None:
    format = 'GTiff'
if infile is None:
    Usage()
if  outfile is None:
    Usage()
    
# =============================================================================
#Try to open input image, and get metadata
indataset = gdal.Open( infile, GA_ReadOnly )
cols, rows = indataset.RasterXSize, indataset.RasterYSize

#need to read band 1 to get data type (Byte, Int16, etc.)
inType = indataset.GetRasterBand(1).DataType

#Get metadata from FITS file
bscale = float(indataset.GetMetadataItem('BSCALE'))
bzero = float(indataset.GetMetadataItem('BZERO'))

#Check to see if user spcified Byte (8 bit) output Type
#The Nodata value is set below
if outType is None:
   outGdalType = inType
else:
   outGdalType = ParseType(outType)

# Read geotransform matrix and calculate ground coordinates
geomatrix = indataset.GetGeoTransform()
X = geomatrix[0]
Y = geomatrix[3]
cellsizeX = geomatrix[1]
cellsizeY = geomatrix[5]

out_driver = gdal.GetDriverByName(format)
if (padLeft or padRight):
   newXSize = padSize
   newYSize = indataset.RasterYSize
   outdataset = out_driver.Create(outfile, newXSize, \
             newYSize, indataset.RasterCount, outGdalType)
else:
   outdataset = out_driver.Create(outfile, indataset.RasterXSize, \
             indataset.RasterYSize, indataset.RasterCount, outGdalType)

outdataset.SetProjection(indataset.GetProjection())

#loop over bands - not needed here but just in case
for band in range (1, indataset.RasterCount + 1):
   iBand = indataset.GetRasterBand(band)
   #if outType is None:
   #   outNoData=iBand.GetNoDataValue()
   outNoData=iBand.GetNoDataValue()
   outband = outdataset.GetRasterBand(band)

   raster_data = iBand.ReadAsArray(0, 0, cols, rows)

   #write out scale and offset to new file
   outband.SetOffset(0)
   outband.SetScale(1)
   if not outNoData is None: 
      outband.SetNoDataValue(outNoData)

   #Apply FITS scale and offset
   if scale:
      raster_data = raster_data * bscale 
      raster_data = raster_data + bzero 
      #outdataset.SetMetadataItem('BSCALE') = 1.0
      #outdataset.SetMetadataItem('BZERO') = 0.0

   #if requested, flip numpy array up-side-down
   if flip:
      raster_data = flipud(raster_data)

   #if requested, set all negative values to NoData (nan)
   if positive:
      raster_data[raster_data<0] = np.nan

   #if requested, set a mask and interpolate over masked values
   if fill:
      mask = np.isnan(raster_data)
      raster_data[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), raster_data[~mask])
      
   #print raster_data.shape
   #output array
   #if requested, set a mask and interpolate over masked values
   if (padLeft or padRight):
      Xoffset = padSize - indataset.RasterXSize
      #Zero out array
      raster_pad = np.zeros((newYSize,Xoffset))
      #print raster_pad.shape

      if padLeft:
         raster_data = np.append(raster_pad,raster_data,axis=1)
      else: #padRight
         raster_data = np.append(raster_data,raster_pad,axis=1)
      #print raster_data.shape

   #write out raster band
   outband.WriteArray(raster_data)

   if not quiet:
      print ("band: " + str(band) + " complete."),

#set output to None to close file
raster_data = None
outdataset = None
indataset = None

