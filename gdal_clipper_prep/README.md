gdal_clipper_prep.py

Name:     gdal_clipper_prep.py 
Project:  GDAL Python Interface
Purpose:  Given a synthesized Europa Clipper (DEM) surface, users can flip,
          apply scale and offset, parameters, map negatives to NoData and
          interpolate over, pad image to the left or right.

          Note: many parameters are hard-wired for our application

Author:   Trent Hare, thare@usgs.gov
Credits:  Based on python GDAL samples 
          http://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/

Usage: gdal_clipper_update.py [-of ENVI] [-flip] [-positive] [-fill] [-scale] [-ot UInt16] [-padLeft] [-padRight] infile.fit outfile.tif
where [ ] are optional parameters

Examples:

% gdal_clipper_prep.py -of ENVI -ot UInt16 -fill -positive -scale -padRight 02L_b_000003.fit 02L_b_000003_pad.raw

% gdal_clipper_prep.py -ot UInt16 -fill -positive -scale -padRight 02L_b_000003.fit 02L_b_000003_pad.tif
