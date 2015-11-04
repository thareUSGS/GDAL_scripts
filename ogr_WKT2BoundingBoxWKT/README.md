ogr2BoundingBoxWKT.py

 Purpose: Given a  WKT geometry, return the extent (4 corners) as a WKT polygon.

 Author: Trent Hare (USGS)
 
 Usage:   ogr_WKT2BoundingBoxWKT.py 'MULTIPOLYGON(((x y, x y, x y, x y,...)))'
 
 
 example run:
%  ogr_WKT2BoundingBoxWKT.py 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)),((20 35, 10 30, 10 10, 30 5, 45 20, 20 35)))'
POLYGON ((10 5 0,45 5 0,45 45 0,10 45 0,10 5 0))
