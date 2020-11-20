fix_jp2
============
description: This routine was specfiically written to update Equirectangular projection keywords targetting HiRISE map projected GeoJpeg2000 images.

routine by Frank Warmerdam
License: public domain.

Purpose: This program attempts to modify the CenterLatGeoKey tag
in a GeoTIFF or GeoJP2 image file to be StandardParallel1GeoKey.
The primarily valuable to fix up GeoJP2's mistakenly generated with
the incorrect parameters for the Equirectangular projection per:
http://trac.osgeo.org/gdal/ticket/2706

How: This routine alters a few bytes in the geotiff section of the *.jp2 files and does not require decompressing and recompressing the jpeg2000 imagery. 

Note fix_jp2.exe has been compiled for Windows and can be used from any commandline terminal window (e.g. cmd, powershell). 

#### Usage:
`fix_jp2 targetfile.jp2`

### tips to compile (using GCC on most all OSs):
`g++ -o fix_jp2 fix_jp2.cpp`

more information also here: https://planetarygis.blogspot.com/2016/07/
more-hirise-conversion-tips-until.html