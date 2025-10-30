Scripts written mostly with help from CoPilot

Purpose: Create a shapefile or GeoJson polygon for the Lunar Prospector "Hydrogen_halfdeg" dataset.
It will work with similarly formatted files, but you might want to change output field name which
is set to "H_ppm". Shapefiles or GeoJSON files can be used within GDAL tools (e.g., ogrinfo or ogr2ogr) 
or directly in applications like QGIS.

**Note this is currently hardwired to the files on the site linked below, which is a lunar decimal degrees "map projection" (IAU_2015:30100).**

Author:  Trent Hare, <trent.m.hare@gmail.com>
Date:    Oct 30, 2025
version: 0.1

Usage: 
`python lp_table2polygon.py hydrogenhd.txt hydrogenhd.shp` 
or
`python lp_table2polygon.py hydrogenhd.txt hydrogenhd.geojson` 

To convert polygons to GeoTIFF
`python shapefile_to_geotiff.py  hydrogenhd.shp hydrogenhd_geo.tif 0.5`

Environment:
installed miniforge, with gdal and geopandas (conda install gdal geopandas).


Data used:
https://pds-geosciences.wustl.edu/missions/lunarp/reduced/hydrogenhd.txt
```
#
# Hydrogen data as described by Feldman et al., JGR, in press, 2001
#
# This file contains 259200 binned values
# for the Lunar Prospector "Hydrogen_halfdeg" dataset of December, 2001.
# These data are in units of H ppm by weight.
#
# Each row contains five columns:
#
#    Lat(min,max)   Lon(min,max)   H ppm by weight
#
# Generated Thu Jan  3 11:39:32 2002 by pds_idl2ascii_dec01.pro v1.1 <djl>
#
  -90.00,    -89.50,   -180.00,   -179.50,      147.49
  -90.00,    -89.50,   -179.50,   -179.00,      147.49
  -90.00,    -89.50,   -179.00,   -178.50,      147.48
  -90.00,    -89.50,   -178.50,   -178.00,      147.47
  -90.00,    -89.50,   -178.00,   -177.50,      147.46
  -90.00,    -89.50,   -177.50,   -177.00,      147.45
…
```