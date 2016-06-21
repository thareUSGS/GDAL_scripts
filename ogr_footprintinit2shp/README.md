footprintinit2shp.py
 Author: Trent Hare (USGS), June 2016

Purpose:  This script converts an caminfo geometry PVL to CSV table with WKT geometry and then into an ESRI Shapefile.
    Projection information can be defined if a WKT projection (prj) file is sent. 

    To create a PVL ready for this tool, in ISIS3 you will need to run:
    (1) spiceinit 
    (2) footprintinit 
    (3) caminfo, using defaults and uselabel=yes; e.g.
    caminfo from=in.cub to=out.pvl uselabel=yes

    Usage: ./footprintinit2shp.py <input.pvl> {projection.prj}
    
	Warning: Column names will be truncated
 
Usage: footprintinit2shp.py <input.pvl> {projection.prj}
 --projection is optional but recommended.

Many projection definitions can be found here:
ftp://pdsimage2.wr.usgs.gov/pub/pigpen/ArcMap_addons/Solar%20System/
note: replace the space in the filename with an underscore before running.

NOTES AND WARNINGS

Note: This code requires Python library PVL: https://pypi.python.org/pypi/pvl
If you are runnning from Anaconda Python you may also need to install pip
```
$ conda install pip
and now that pip is intalled you can get pvl.
$ pip install pvl
```

Warning: Unfortunately the older GIS vector format shapfile doesn't like long field names. When the conversion runs, ogr2ogr will automatically map the long fields into a short field names. Just copy the mapping down (if you need the long names). QGIS likes GML too but the projection isn't carried over...? ogr2ogr supports several database formats too but then you have to set that up first before loading. Anyway, use shapefile for now.

To run in batch:

```
tcsh 
       if not running a csh/tcsh
foreach i (*.pvl)
foreach? ./footprintinit2shp.py $i Enceladus_2009.prj
foreach? end
```

note: you will get lots of field map warnings (copy the last run into a text file so you know the original name). The .vrt(s), .csv(s) .csvt(s) can now be deleted.  Shapefiles will have a *.shp, *.dbf, *.shx, and *.prj (at a minimum). Load the *.shp into ArcMap or QGIS. 

To merge them all into one shapefile.
```
foreach i (*.shp)
foreach? ogr2ogr -update -append 00_merged.shp -f "ESRI Shapefile" $i
foreach? end
```
