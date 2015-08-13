Astropedia_gdal2ISIS3.py

Aug 2015, Trent Hare, USGS, thare@usgs.gov

Purpose: Create a ISIS3 compatible (raw w/ ISIS3 label) from a GDAL supported image.
Author:  Trent Hare, <thare@usgs.gov>
Date:    June 05, 2013
version: 0.1

Port from gdalinfo.py whose author is Even Rouault
Copyright (c) 2010, Even Rouault
Copyright (c) 1998, Frank Warmerdam


Usage: Astropedia_gdal2ISIS3.py in.tif output.cub
   optional: to print out image information also send -debug
   optional: to just get a label *.lbl, send -noimage
   optional: to get lonsys=360, send -force360
   optional: to override the center Longitude, send -centerLon 180
   optional: to set scaler and offset send -base 17374000 and/or -multiplier 0.5
Usage: Astropedia_gdal2ISIS3.py -debug in.cub output.cub
Note: Currently this routine will only work for a limited set of images
