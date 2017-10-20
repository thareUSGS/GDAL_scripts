PDS4 example scripts for GDAL
============

These simple scripts show a short example for reading an ISIS3 label and creating a conversion configuation file for a minimal converson from ISIS3 to PDS4.

The test example is the LOLA 4ppd DEM as converted to an ISIS3 cube from the PDS:
http://pds-geosciences.wustl.edu/missions/lro/lola.htm

**Usage:**
```
python isis3_to_pds4_LOLA_pvl.py input.cub output.config
   optional: to run gdal_translate send: -run
   optional: to set a PDS4 XML template send: -template my.xml
      by default the template used is from $GDALDATA/pds4_template.xml

Usage: isis3_to_pds4_LOLA.py -run -template myTemplate.xml in.cub out.config
Note: Requires an existing PDS4 XML template with known variables.
```

**Example run:**
```
> python isis3_to_pds4_LOLA_pvl.py ldem_4.cub ldem_4.config
writing ldem_4.config
No ObservationId in ISIS3 Label
No FileName in ISIS3 Label

Recommended gdal run:
gdal_translate -of PDS4 -co IMAGE_FORMAT=GEOTIFF -co TEMPLATE=pds4_template.xml --optfile ldem_4.config ldem_4.cub ldem_4_pds4.xml

> cat ldem_4.config
#run as isis3_to_pds4_LOLA_pvl.py ldem_4.cub ldem_4.config
-co VAR_TARGET_TYPE=Satellite
-co VAR_INVESTIGATION_AREA_LID_REFERENCE="urn:nasa:pds:context:instrument_host:spacecraft.lro"
-co VAR_TARGET=MOON
-co VAR_INVESTIGATION_AREA_NAME="LUNAR RECONNAISSANCE ORBITER"
-co VAR_LOGICAL_IDENTIFIER=LRO-L-LOLA-4-GDR-V1.0
-co VAR_OBSERVING_SYSTEM_NAME=LOLA
-co VAR_TITLE=LDEM_4

```

As of Oct. 2017, this requires very recent builds (meaning daily trunk) for GDAL. For more information for the new GDAL PDS4 driver (beta) see: http://www.gdal.org/frmt_pds4.html As a new driver and new format, please report any issues to the bug tracker, as explained on the wiki: https://trac.osgeo.org/gdal/wiki