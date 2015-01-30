#!/usr/bin/env python
#******************************************************************************
#  $Id$
#  Name:     gdal_baseline_slope.py 
#  Project:  GDAL Python Interface
#  Purpose:  Given a DEM, calculate specialized slopes using various baseline
#            lengths (1 baseline, 2 baseline, 5 baseline). Also a more normal
#            slope equation is available.
#  Author:   Trent Hare, thare@usgs.gov
#  Credits:  Based on python GDAL samples 
#            http://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/
#            and scipy slope example from om_henners
#            http://gis.stackexchange.com/questions/18319/calculating-slope-cell-by-cell-in-arcpy
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

from scipy.ndimage import generic_filter

# =============================================================================
# Usage()

def Usage():
    print("""
Usage: gdal_baseline_slope.py -baseline n -ot outputType infile outfile 
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

# =============================================================================
# This section contains functions that can be sent to
# scipy generic_filter function.

def calc_slope_baseline1(in_filter, x_cellsize, y_cellsize, outNoData):
    if outNoData in in_filter:
        return outNoData #will return NoData around edge
    else:
        [a, b, c, d] = in_filter
        #From 2x2 box, row 1: a, b
        #              row 2: c, d

        dz_dx = ((b + d) - (a + c)) / (2.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (2.0 * float(y_cellsize))

        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #we want slope in degrees rather than radians
    
def calc_slope_baseline2(in_filter, x_cellsize, y_cellsize, outNoData):
    if outNoData in in_filter:
        return outNoData #will return NoData around edge
    else:
        #From 3x3 box, but note we are only using 4 corners in calculation
        #which is why the variables are named out of order
        [a, q, b, r, s, t, c, u, d] = in_filter
        #From 3x3 box, row 1: a, q, b
        #              row 2: r, s, t
        #              row 3: c, u, d

        dz_dx = ((b + d) - (a + c)) / (4.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (4.0 * float(y_cellsize))
        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #we want slope in degrees rather than radians
    
def calc_slope_baseline5(in_filter, x_cellsize, y_cellsize, outNoData):
    if outNoData in in_filter:
        return outNoData #will return NoData around edge
    else:
        #From 6x6 box, but note we are only using 4 corners in calculation
        #which is why the variables are named out of order
        [ a, q1, r1, s1, t1,  b, 
          g,  h,  i,  j,  k,  l, 
          m,  n,  o,  p,  q,  r, 
          s,  t,  u,  v,  w,  x, 
          y,  z, a1, b1, c1, d1, 
          c, f1, g1, h1, i1,  d] = in_filter
         
        dz_dx = ((b + d) - (a + c)) / (10.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (10.0 * float(y_cellsize))

        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #we want slope in degrees rather than radians

def calc_slope(in_filter, x_cellsize, y_cellsize, outNoData):
    #more normal slope calculation here - default if baseline flag is not sent.
    if outNoData in in_filter:
        return outNoData #will return NoData around edge with mode constane 
    else:
        [a, b, c, d, e, f, g, h, i] = in_filter
        #From 3x3 box, row 1: a, b, c
        #              row 2: d, e, f
        #              row 3: g, h, i

        dz_dx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * float(x_cellsize))
        dz_dy = ((g + 2.0 * h + i) - (a + 2.0 * b + c)) / (8.0 * float(y_cellsize))
        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(slope) #we want slope in degrees rather than radians

# =============================================================================
# 	Mainline
# =============================================================================
argv = gdal.GeneralCmdLineProcessor( sys.argv )

infile = None
outfile = None
baseline = None
otype = None
quiet = False

#output format currently hardwired to Tiff output
format = 'GTiff'

# set up some default nodatavalues for each datatype
NoDataLookup={'Byte':0, 'UInt16':0, 'Int16':-32768, 'UInt32':0, \
   'Int32':-2147483647, 'Float32':-3.402823466E+38, 'Float64':1.7976931348623158E+308}

# Parse command line arguments.
i = 1
while i < len(sys.argv):
    arg = argv[i]
    if arg == '-baseline':
        i = i + 1
        baseline = int(argv[i])
    elif arg == '-q' or arg == '-quiet':
        quiet = True
    elif infile is None:
        infile = arg
    elif outfile is None:
        outfile = arg
    else:
        Usage()
    i = i + 1

if infile is None:
    Usage()
if  outfile is None:
    Usage()
if baseline is None:
    baseline = 3
    print "Warning: baseline defaulting to 3, send -baseline VALUE to set a different value."
    
#Try to open input image
indataset = gdal.Open( infile, GA_ReadOnly )

#need to read band 1 to get data type (Byte, Int16, etc.)
type = indataset.GetRasterBand(1).DataType
newType = ParseType(type)

#define output format, name, size, type mostly based on input image
#we are not setting any projection since this a gore image
out_driver = gdal.GetDriverByName(format)
outdataset = out_driver.Create(outfile, indataset.RasterXSize, \
             indataset.RasterYSize, indataset.RasterCount, type)
outdataset.SetProjection(indataset.GetProjection())

cols, rows = indataset.RasterXSize, indataset.RasterYSize

# Read geotransform matrix and calculate ground coordinates
geomatrix = indataset.GetGeoTransform()
X = geomatrix[0]
Y = geomatrix[3]

# X cellsize
cellsizeX = geomatrix[1]
# Y cellsize
cellsizeY = geomatrix[5]
#if not quiet:
#   print "cellsize in X,Y: " + str(cellsizeX) +"," + str(cellsizeY)

#loop over bands -- probably can handle all bands at once...
for band in range (1, indataset.RasterCount + 1):
   iBand = indataset.GetRasterBand(band)
   outNoData=iBand.GetNoDataValue()

   outband = outdataset.GetRasterBand(band)
   outband.SetNoDataValue(outNoData)

   if not quiet:
      print ("band: " + str(band) + ", "),
    
   raster_data = iBand.ReadAsArray(0, 0, cols, rows)
   #data = iBand.ReadRaster(0, 0, cols, rows, buf_type=gdal.GDT_Float32)
   #raster_data = np.fromstring(data, dtype=np.float32).reshape(rows, cols)

   if baseline == 1:
      slope = generic_filter(raster_data, calc_slope_baseline1, size=2, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      #shift half a pixel to center 
      #newGeomatrix = (X + (0.5 * cellsizeX), geomatrix[1], geomatrix[2], Y + (0.5 * cellsizeY), geomatrix[4], geomatrix[5])
      #outdataset.SetGeoTransform(newGeomatrix)
      outdataset.SetGeoTransform(indataset.GetGeoTransform())
   elif baseline == 2:
      slope = generic_filter(raster_data, calc_slope_baseline2, size=3, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      outdataset.SetGeoTransform(indataset.GetGeoTransform())
   elif baseline == 5:
      slope = generic_filter(raster_data, calc_slope_baseline5, size=6, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      #shift half a pixel to center 
      #newGeomatrix = (X + (0.5 * cellsizeX), geomatrix[1], geomatrix[2], Y + (0.5 * cellsizeY), geomatrix[4], geomatrix[5])
      #outdataset.SetGeoTransform(newGeomatrix)
      outdataset.SetGeoTransform(indataset.GetGeoTransform())
   else:
      slope = generic_filter(raster_data, calc_slope, size=3, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      outdataset.SetGeoTransform(indataset.GetGeoTransform())

   #write out band to new file
   outband.WriteArray(slope)

   #update progress line
   #if not quiet:
   #   gdal.TermProgress( 1.0 - (float(band) / indataset.RasterCount ))

#set output to None to close file
outdataset = None
indataset = None
