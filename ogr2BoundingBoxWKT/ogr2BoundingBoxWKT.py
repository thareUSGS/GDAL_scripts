#!/usr/bin/env python

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
    print("Usage: ogr2BoundingBoxWKT.py 'MULTIPOLYGON(((x y, x y, x y, x y)))'\n")
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
   print
   print poly

if __name__ == "__main__":
    main(sys.argv)

