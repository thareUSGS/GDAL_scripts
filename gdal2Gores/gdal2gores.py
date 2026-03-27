#!/usr/bin/env python
#******************************************************************************
#  $Id$
#  Name:     gdal2gores.py 
#  Project:  GDAL Python Interface
#  Purpose:  Given a Simple Cylindrical map projected image remap to an image with n gores.
#            for placing map or printing map on a sphere (e.g. tennis ball). 
#            I'm sure this could be optimized!
#  Author:   Trent Hare, thare@usgs.gov
#  Credits:  Based on C# implementation by winski software or
#            Michal Wisniewski,  http://winski.x10.mx/?page_id=2
#            and python GDAL samples, 
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

# =============================================================================
# Usage()

def Usage():
    print("""
Usage: gdal2gores.py -ng number_of_gores infile outfile 
""")
    sys.exit(1)
    
# =============================================================================
# 	Mainline
# =============================================================================
argv = gdal.GeneralCmdLineProcessor( sys.argv )

infile = None
outfile = None
gores = None
quiet = False
#current hardwired to Tiff output
format = 'GTiff'

# Parse command line arguments.
i = 1
while i < len(sys.argv):
    arg = argv[i]
    if arg == '-ng':
        i = i + 1
        gores = int(argv[i])
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
if gores is None:
    gores = 8
    print("Warning: Number of gores defaulting to 8, send -nd VALUE to set a different value.")
    
#Try to open input image
in_dataset = gdal.Open( infile, GA_ReadOnly )

#need to read band 1 to get data type (Byte, Int16, etc.)
type = in_dataset.GetRasterBand(1).DataType

#define output format, name, size, type mostly based on input image
#we are not setting any projection since this a gore image
out_driver = gdal.GetDriverByName(format)
outdataset = out_driver.Create(outfile, in_dataset.RasterXSize, \
             in_dataset.RasterYSize, in_dataset.RasterCount, type)

#gore parameters
goreWidth = in_dataset.RasterXSize // gores;

#loop over bands -- probably can handle all bands at once...
for band in range (1, in_dataset.RasterCount + 1):
   iBand = in_dataset.GetRasterBand(band)
   outband = outdataset.GetRasterBand(band)
 
   if not quiet:
      print ("band: " + str(band) + ", "),

   #loop over lines so we can handle huge images
   for y in range(iBand.YSize - 1, -1, -1):
      #load whole line as array
      inline = iBand.ReadAsArray(0, y, iBand.XSize, 1, iBand.XSize, 1)

      #inititialize output array to zeros
      dstline = np.asarray([0] * iBand.XSize)

      goreStart = 0;
      goreCenter = goreWidth/2;

      # iterate over each gore as specified by the user
      # based on C# implementation by winski software
      for i in range(gores):

         # iterate over each pixel in output gore
         for x in range(goreWidth):
            dn = inline[0, goreStart + x]
            # set new position for pixel value in output array
            # updated with round to increase overlap at gore edge
            newX = int(round(goreCenter + math.cos((-math.pi/2.0) + (math.pi * float(y) / float(iBand.YSize))) \
                       * (x - (goreWidth / 2.0))))
            dstline[newX] = dn
 
         # move start and center to the correct places
         goreStart = goreStart + goreWidth
         goreCenter =  goreCenter + goreWidth

      #write out scanline for the current band
      out_array = np.asarray([dstline])
      outband.WriteArray(out_array, 0, y)

      #update progress line
      if not quiet:
         gdal.TermProgress( 1.0 - (float(y) / iBand.YSize ))

#set output to None to close file
outdataset = None
