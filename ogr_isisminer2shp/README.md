isisminer2shp.py

Purpose:  This script converts an isisminer CSV table with WKB geometry into an ESRI Shapefile.
The projection information is retained if prj file is sent. Column names will be truncated
 
 Author: Trent Hare (USGS), June 2016
 
Usage: isisminer2shp.py <input.csv> {projection.prj}
 --projection is optional but recommended.

Many projection definitions can be found here:
ftp://pdsimage2.wr.usgs.gov/pub/pigpen/ArcMap_addons/Solar%20System/
note: replace the space in the filename with an underscore before running.

NOTES AND WARNINGS

Warning: Unfortunately the older GIS vector format shapfile doesn't like long field names. When the conversion runs, ogr2ogr will automatically map the long fields into a short field names. Just copy the mapping down (if you need the long names). QGIS likes GML too but the projection isn't carried over...? ogr2ogr supports several database formats too but then you have to set that up first before loading. Anyway, use shapefile for now.

I currently create a .csvt for the type of fields but I'm not sure if the type or number of fields change. I would recommend that isisminer could create a ".csvt" which is a single line that maps the field type for CSV files. e.g. 
"String", "String", "Real", "Integer", "Real", ....

To run in batch:

 -tcsh 
       if not running a csh/tcsh
-foreach i (*.csv)
-foreach? /usgs/cdev/contrib/bin/isisminer2shp.py $i /usgs/shareall/thare/projections/Enceladus_2009.prj
-foreach? end

note: you will get lots of field map warnings (copy the last run into a text file so you know the original name). The *.vrt(s) can now be deleted.  Shapefiles will have a *.shp, *.dbf, *.shx, and *.prj (at a minimum). Load the *.shp into ArcMap or QGIS. 

To merge them all into one shapefile.
-foreach i (*.shp)
-foreach? ogr2ogr -update -append 00_merged.shp -f "ESRI Shapefile" $i
-foreach? end
