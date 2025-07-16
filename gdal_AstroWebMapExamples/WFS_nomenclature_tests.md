## WFS API (Mapserver) for USGS IAU Nomenclature PostgreSQL/PostGIS database 
_Not officially supported. Use at your own risk_

Note: for compatiblity with mapping interfaces, all planetary WFS layers are tagged in degrees but using an Earth definition (EPSG:4326, WGS84)! 
---
- listing from from: https://astrowebmaps.wr.usgs.gov/webmapatlas/Layers/maps.html

### Mars Examples
- getcapabilities:
https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&REQUEST=getcapabilities
---
- form QGIS: https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map
- GML points:
https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POINT&REQUEST=getfeature&BBOX=10,5,65,25
- GML polys (_could have wrapping issues_):
https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POLY&REQUEST=getfeature&BBOX=50,5,65,15
---
- GeoJSON: https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POINT&REQUEST=getfeature&OUTPUTFORMAT=geojson
- GeoJSON w/ BBOX: https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POINT&REQUEST=getfeature&BBOX=10,5,65,25&OUTPUTFORMAT=geojson
- GeoJSON, just two fields: https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=MARS_POINT&REQUEST=getfeature&OUTPUTFORMAT=geojson&propertyname=feature,diameter
---
- ZIP shapefile:
https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POINT&REQUEST=getfeature&BBOX=10,5,65,25&OUTPUTFORMAT=SHAPEZIP 
---
CSV:
https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/mars/mars_nomen_wfs.map&service=WFS&version=1.1.0&TYPENAME=ms:MARS_POINT&REQUEST=getfeature&BBOX=10,5,65,25&OUTPUTFORMAT=CSV
