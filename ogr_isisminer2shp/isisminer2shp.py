#!/usr/bin/env python
#Purpose: To convert from isisminer CSV geo=WKB to a shapefile
# Trent Hare

#from osgeo import ogr
import sys, os, time

def Usage():
    print '''
    This script converts an isisminera CSV table with WKB geometry into an ESRI Shapefile.
    projection information is retained if prj file is sent. Column names will be truncated
    
    Usage: %s <input.csv> {projection.prj}
    '''%sys.argv[0]
    
if len(sys.argv) < 2:
    Usage()
    sys.exit(0)

#Open the csv file to read
try:
    input = sys.argv[1]
    inputNoExt = os.path.splitext(input)[0]
    outputVRT = inputNoExt+'.vrt'
    outputShp = inputNoExt+'.shp'
    outputCsvt = inputNoExt+'.csvt'
except:
    Usage()
    sys.exit(1)

#grab projection
projection = None
if len(sys.argv) > 2:
   projection = sys.argv[2]

#input_format = sys.argv[3]

#Create isisminer CSVT (type mappin gfor fields) - Does this change...?
fieldMapping = '"String","String","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","String","String","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","Real","String"'
target = open(outputCsvt, 'w')
target.write(fieldMapping)
target.write('\n')
target.close()

#Create an VRT layer
target = open(outputVRT, 'w')
target.write('<OGRVRTDataSource>\n')
target.write('  <OGRVRTLayer name="%s">\n' % (inputNoExt))
target.write('    <SrcDataSource>%s</SrcDataSource>\n' % (input))
target.write('    <GeometryType>wkbPolygon</GeometryType>\n')
#target.write('    <LayerSRS>GEOGCS["Enceladus 2009",DATUM["D_Enceladus_2009",SPHEROID["Enceladus_2009_IAU_IAG",252100.0,0.0]],PRIMEM["Reference_Meridian",0],UNIT["Decimal_Degree",0.0174532925199433],AUTHORITY["IAU2009","60200"]]</LayerSRS>

#Default projection to help define it is degrees. User should send *.prj
target.write('    <LayerSRS>WGS84</LayerSRS>\n')
target.write('    <GeometryField encoding="WKB" field="GisFootprint"/>\n')
target.write('  </OGRVRTLayer>\n')
target.write('</OGRVRTDataSource>\n')
target.close()

while os.path.isfile(outputVRT) == False:
    time.sleep(10)
    print "sleeping"

#convert VRT using ogr2ogr
if projection is None:
  print 'No projection sent, defaulting to WGS84 (degrees)'
  os.system('ogr2ogr -f "ESRI Shapefile" -overwrite -skipfailures -oo AUTODETECT_TYPE=YES -oo HEADERS=YES %s %s' % (outputShp,outputVRT))  
else:
  os.system('ogr2ogr -f "ESRI Shapefile" -a_srs %s -overwrite -skipfailures -oo AUTODETECT_TYPE=YES -oo HEADERS=YES %s %s' % (projection,outputShp,outputVRT))  

if os.path.isfile(outputShp):
  print 'shapefile created: %s ' % (outputShp)
else:
  print 'shapefile not created'

