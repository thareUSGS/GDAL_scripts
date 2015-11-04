#!/usr/bin/env python

# Purpose: Given a  WKT geometry, return the extent (4 corners) as a WKT polygon.
# Author: Trent Hare (USGS)
# November 4, 2015

import sys
try:
    from osgeo import gdal
    from osgeo import ogr
except:
    import gdal
    import ogr

#/************************************************************************/
#/*                               Usage()                                */
#/************************************************************************/
def Usage():
    print("Usage: ogr_WKT2BoundingBoxWKT.py 'MULTIPOLYGON(((x y, x y, x y, x y)))'\n")
    return 1

#/************************************************************************/
#/*                                main()                                */
#/************************************************************************/
def main( argv ):

#/* -------------------------------------------------------------------- */
#/*      Parse arguments.                                                */
#/* -------------------------------------------------------------------- */
   if len(argv) == 2:
      wkt = argv[1]
   else:
      return Usage()

   geom = ogr.CreateGeometryFromWkt(wkt)

   # Get Envelope returns a tuple (minX, maxX, minY, maxY)
   extent = geom.GetEnvelope()

   # Create a Polygon from the extent tuple
   ring = ogr.Geometry(ogr.wkbLinearRing)
   ring.AddPoint(extent[0],extent[2])
   ring.AddPoint(extent[1], extent[2])
   ring.AddPoint(extent[1], extent[3])
   ring.AddPoint(extent[0], extent[3])
   ring.AddPoint(extent[0],extent[2])
   poly = ogr.Geometry(ogr.wkbPolygon)
   poly.AddGeometry(ring)
   #print ('Polygon area =',poly.GetArea() )
   print poly.ExportToWkt()

if __name__ == "__main__":
    main(sys.argv)

