#!/usr/bin/env python
#******************************************************************************
#  $Id$
#  Name:     gdal_baseline_slope.py 
#  Project:  GDAL Python Interface
#  Purpose:  Given a DEM, calculate specialized slopes using various baseline
#            lengths (1 baseline, 2 baseline, 5 baseline) as defined by R. Kirk. 
#            The more commonly-used Horn's Method is also available.
#  Author:   Trent Hare, thare@usgs.gov
#  Credits:  Based on python GDAL samples 
#            http://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/
#            and scipy slope example from om_henners
#            https://github.com/om-henners/ndimage_talk/blob/master/calculate_slope.py
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

from scipy.ndimage import generic_filter

# =============================================================================
# Usage()
def Usage():
    print("""
Usage: gdal_baseline_slope.py [-baseline 1,2,5] [-ot Byte] [-crop]  infile outfile.tif
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
# This section contains functions that can be sent to
# scipy generic_filter function.
#
# Future: make filter assignment variable nt just 1,2, and 5

def calc_slope_baseline1(in_filter, x_cellsize, y_cellsize, noData):
    if noData in in_filter:
        return noData #will return NoData around edge
    else:
        #From 2x2 box, 
        [a, b,
         c, d] = in_filter

        dz_dx = ((b + d) - (a + c)) / (2.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (2.0 * float(y_cellsize))

        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #we want slope in degrees rather than radians
    
def calc_slope_baseline2(in_filter, x_cellsize, y_cellsize, noData):
    if noData in in_filter:
        return noData #will return NoData around edge
    else:
        #From 3x3 box, but note we are only using 4 corners in calculation
        #which is why a dummy "z" variable is present
        [a, z, b,
         z, z, z,
         c, z, d] = in_filter

        dz_dx = ((b + d) - (a + c)) / (4.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (4.0 * float(y_cellsize))
        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #return slope in degrees rather than radians
    
def calc_slope_baseline5(in_filter, x_cellsize, y_cellsize, noData):
    if noData in in_filter:
        return noData #will return NoData around edge
    else:
        #From 6x6 box, but note we are only using 4 corners in calculation
        #which is why a dummy "z" variable is present
        [ a,  z,  z,  z,  z,  b, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          c,  z,  z,  z,  z,  d] = in_filter
         
        dz_dx = ((b + d) - (a + c)) / (10.0 * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (10.0 * float(y_cellsize))

        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #return slope in degrees rather than radians

def calc_slope(in_filter, x_cellsize, y_cellsize, noData):
    # Use Horn's Method for slope calculation here - default if -baseline flag is not sent.
    # This is equivalent to the commandline utility 'gdaldem slope'
    if noData in in_filter:
        return noData #will return NoData around edge beacuse mode=constant 
    else:
        #From 3x3 box, 
        [a, b, c,
         d, e, f,
         g, h, i] = in_filter

        dz_dx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * float(x_cellsize))
        dz_dy = ((g + 2.0 * h + i) - (a + 2.0 * b + c)) / (8.0 * float(y_cellsize))
        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #return slope in degrees rather than radians

# =============================================================================
# 	Mainline
# =============================================================================
argv = gdal.GeneralCmdLineProcessor( sys.argv )

infile = None
outfile = None
baseline = None
outType = None
outNoData = None
crop = False
quiet = False

#output format currently hardwired to Tiff output
format = 'GTiff'

# Parse command line arguments.
i = 1
while i < len(sys.argv):
    arg = argv[i]
    if arg == '-baseline':
        i = i + 1
        baseline = int(argv[i])
    elif arg == '-ot':
        i = i + 1
        outType = argv[i]
    elif arg == '-c' or arg == '-crop':
        crop = True
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
    print ("Warning: Using Horn's method for slope calculation, send -baseline VALUE [1,2,5] to set specialized calculation.")
    
# =============================================================================
#Try to open input image, and get metadata
indataset = gdal.Open( infile, GA_ReadOnly )
cols, rows = indataset.RasterXSize, indataset.RasterYSize

#need to read band 1 to get data type (Byte, Int16, etc.)
inType = indataset.GetRasterBand(1).DataType

#Check to see if user spcified Byte (8 bit) output Type
#The Nodata value is set below
if outType is None:
   outGdalType = inType
else:
   outGdalType = ParseType(outType)
   outfile8 = outfile
   outfile = "32bit_"+outfile

if crop:
   cropfile = outfile
   outfile = "temp_"+outfile
   cropfile8 = outfile8
   outfile8 = "temp_"+outfile8

# Read geotransform matrix and calculate ground coordinates
geomatrix = indataset.GetGeoTransform()
X = geomatrix[0]
Y = geomatrix[3]
cellsizeX = geomatrix[1]
cellsizeY = geomatrix[5]

# shift amount for baseline = 1 
X1 = X - (cellsizeX / 2.0)
Y1 = Y - (cellsizeY / 2.0)

# shift amount for baseline = 2 
# No shift

# shift amount for baseline = 5 
X5 = X - (cellsizeX / 2.0)
Y5 = Y - (cellsizeY / 2.0)

#define output format, name, size, type mostly based on input image
#this is meant for 32bit ourput file
out_driver = gdal.GetDriverByName(format)
outdataset = out_driver.Create(outfile, indataset.RasterXSize, \
             indataset.RasterYSize, indataset.RasterCount, inType)
outdataset.SetProjection(indataset.GetProjection())

if outType == 'Byte': 
   outdataset8 = out_driver.Create(outfile8, indataset.RasterXSize, \
             indataset.RasterYSize, indataset.RasterCount, outGdalType)
   outdataset8.SetProjection(indataset.GetProjection())

#loop over bands -- probably can handle all bands at once...
for band in range (1, indataset.RasterCount + 1):
   iBand = indataset.GetRasterBand(band)
   #if outType is None:
   #   outNoData=iBand.GetNoDataValue()
   outNoData=iBand.GetNoDataValue()
   outband = outdataset.GetRasterBand(band)
   if outType == 'Byte': 
      outband8 = outdataset8.GetRasterBand(band)

   raster_data = iBand.ReadAsArray(0, 0, cols, rows)
   if baseline == 1:
      slope = generic_filter(raster_data, calc_slope_baseline1, size=2, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      #shift half a pixel to center 
      newGeomatrix = (X1 , geomatrix[1], geomatrix[2], Y1, geomatrix[4], geomatrix[5])
      outdataset.SetGeoTransform(newGeomatrix)
      if outType == 'Byte': 
         outdataset8.SetGeoTransform(newGeomatrix)
   elif baseline == 2:
      slope = generic_filter(raster_data, calc_slope_baseline2, size=3, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      outdataset.SetGeoTransform(indataset.GetGeoTransform())
      if outType == 'Byte': 
         outdataset8.SetGeoTransform(indataset.GetGeoTransform())
   elif baseline == 5:
      slope = generic_filter(raster_data, calc_slope_baseline5, size=6, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      #shift half a pixel to center 
      newGeomatrix = (X5 , geomatrix[1], geomatrix[2], Y5, geomatrix[4], geomatrix[5])
      outdataset.SetGeoTransform(newGeomatrix)
      if outType == 'Byte': 
         outdataset8.SetGeoTransform(newGeomatrix)
   else:
      slope = generic_filter(raster_data, calc_slope, size=3, mode='constant',
                       cval=outNoData, extra_arguments=(cellsizeX, cellsizeY, outNoData))
      outdataset.SetGeoTransform(indataset.GetGeoTransform())
      if outType == 'Byte': 
         outdataset8.SetGeoTransform(indataset.GetGeoTransform())

   #write out band to new file
   outband.SetOffset(0)
   outband.SetScale(1)
   outband.SetNoDataValue(outNoData)
   outband.WriteArray(slope)

   #write out raster data
   if outType == 'Byte': #if Byte (8bit), scale slope degrees to 1 to 255).
      slope[slope == iBand.GetNoDataValue()] = np.nan
      # NOTE: The choice of scale factor and offset below deliberately maps slopes >50 degrees to 255
      slope_8bit = np.round((slope + 0.2) * 5.0)
      slope_masked = np.where(np.isnan(slope), 0, slope_8bit)
      outband8.SetOffset(-0.2)
      outband8.SetScale(0.2)
      outband8.SetNoDataValue(0) # should be 0
      outband8.WriteArray(slope_masked)

   if not quiet:
      print ("band: " + str(band) + " complete."),

#check to see if user wants to crop, this optional step emulates Randy's code
#Future: clean up, essentailly an extra step is added which isn't really needed
if (crop and (baseline != 3)):
   #define output format, name, size, type mostly based on input image
   #cropped dimensions are input minus baseline
   newXSize = outdataset.RasterXSize - baseline
   newYSize = outdataset.RasterYSize - baseline
   cropdataset = out_driver.Create(cropfile, newXSize, newYSize, \
                 outdataset.RasterCount, inType)
   cropdataset.SetProjection(outdataset.GetProjection())
   if outType == 'Byte': 
      cropdataset8 = out_driver.Create(cropfile8, newXSize, newYSize, \
                 outdataset.RasterCount, outGdalType)
      cropdataset8.SetProjection(outdataset.GetProjection())
   print "cropping file with %d less pixels X=%d, Y=%d" % (baseline, newXSize, newYSize)

   # Read geotransform matrix and calculate ground coordinates
   geomatrix = outdataset.GetGeoTransform()
   X = geomatrix[0]
   Y = geomatrix[3]
   cellsizeX = geomatrix[1]
   cellsizeY = geomatrix[5]

   for band in range (1, outdataset.RasterCount + 1):
      iBand = outdataset.GetRasterBand(band)
      cropBand = cropdataset.GetRasterBand(band)
      if outType == 'Byte': 
         iBand8 = outdataset8.GetRasterBand(band)
         cropBand8 = cropdataset8.GetRasterBand(band)
      if baseline == 1:
         #no shift just removeing pixel from right and bottom
         #raster_data = iBand.ReadAsArray(0, 0, cols - 1, rows - 1)
         cropBand.WriteArray(slope[1:,1:])
         X1 = X + cellsizeX
         Y1 = Y + cellsizeY
	 newGeomatrix = (X1 , geomatrix[1], geomatrix[2], Y1, geomatrix[4], geomatrix[5])
	 cropdataset.SetGeoTransform(newGeomatrix)
         if outType == 'Byte': 
            cropBand8.WriteArray(slope_masked[1:,1:])
	    cropdataset8.SetGeoTransform(newGeomatrix)
      elif baseline == 2:
         #shift 1 pixel in and remove pixel from right/bottom
         #raster_data = iBand.ReadAsArray(1, 1, cols - 1, rows - 1)
         cropBand.WriteArray(slope[1:-1,1:-1])
         X2 = X + cellsizeX
         Y2 = Y + cellsizeY
         newGeomatrix = (X2 , geomatrix[1], geomatrix[2], Y2, geomatrix[4], geomatrix[5])
         cropdataset.SetGeoTransform(newGeomatrix)
         if outType == 'Byte': 
            cropBand8.WriteArray(slope_masked[1:-1,1:-1])
            cropdataset8.SetGeoTransform(newGeomatrix)
      elif baseline == 5:
         #shift 2 pixel in and remove 2 pixels from right/bottom
         #raster_data = iBand.ReadAsArray(2, 2, cols - 3, rows - 3)
         cropBand.WriteArray(slope[3:-2,3:-2])
         X5 = X + (cellsizeX * 3)
         Y5 = Y + (cellsizeY * 3)
         newGeomatrix = (X5 , geomatrix[1], geomatrix[2], Y5, geomatrix[4], geomatrix[5])
         cropdataset.SetGeoTransform(newGeomatrix)
         if outType == 'Byte': 
            cropBand8.WriteArray(slope_masked[3:-2,3:-2])
            cropdataset8.SetGeoTransform(newGeomatrix)
      else:
         print "This baseline not supported during a crop\n"

      cropBand.SetNoDataValue(iBand.GetNoDataValue())
      cropBand.SetScale(iBand.GetScale())
      cropBand.SetOffset(iBand.GetOffset())
      if outType == 'Byte': 
         cropBand8.SetNoDataValue(iBand8.GetNoDataValue())
         cropBand8.SetScale(iBand8.GetScale())
         cropBand8.SetOffset(iBand8.GetOffset())

   cropdataset = None
   outdataset = None
   os.remove(outfile)
   if outType == 'Byte': 
      cropdataset8 = None
      outdataset8 = None
      os.remove(outfile8)
    
#set output to None to close file
raster_data = None
outdataset = None
outdataset8 = None
indataset = None

