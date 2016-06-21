#!/usr/bin/env python
# Title: footprintinit2shp.py
# Purpose: To convert a PVL from caminfo (geometry) to CSV geo=WKT and then to a shapefile
# Trent Hare
# Original: June 2016

#from osgeo import ogr
import sys, os, time
import pvl

def Usage():
    print '''
    This script converts an caminfo geometry PVL to CSV table with WKT geometry into an ESRI Shapefile.
    Projection information can be defined if a WKT projection (prj) file is sent. 

    To create a PVL ready for this tool, in ISIS3 you will need to run:
    (1) spiceinit 
    (2) footprintinit 
    (3) caminfo, using defaults and uselabel=yes; e.g.
    caminfo from=in.cub to=out.pvl uselabel=yes

    Warning: Column names will be truncated
    
    Usage: %s <input.pvl> {projection.prj}
    '''%sys.argv[0]
    
if len(sys.argv) < 2:
    Usage()
    sys.exit(0)

#Open the csv file to read
try:
    input = sys.argv[1]
    inputNoExt = os.path.splitext(input)[0]
    outputVRT  = inputNoExt+'.vrt'
    outputShp  = inputNoExt+'.shp'
    outputCsv  = inputNoExt+'.csv'
    outputCsvt = inputNoExt+'.csvt'
except:
    Usage()
    sys.exit(1)

#grab projection
projection = None
if len(sys.argv) > 2:
   projection = sys.argv[2]

#input_format = sys.argv[3]

###########################
#Convert caminfo PVL to CSV

#load ISIS label using PVL library
label = pvl.load(input)
Filename = label['Caminfo']['Parameters']['From']

#Get Geometry section
StartTime = repr(label['Caminfo']['Geometry']['StartTime'])
EndTime = repr(label['Caminfo']['Geometry']['EndTime'])
CenterLine = repr(label['Caminfo']['Geometry']['CenterLine'])
CenterSample = repr(label['Caminfo']['Geometry']['CenterSample'])
CenterLatitude = repr(label['Caminfo']['Geometry']['CenterLatitude'])
CenterLongitude = repr(label['Caminfo']['Geometry']['CenterLongitude'])
CenterRadius = repr(label['Caminfo']['Geometry']['CenterRadius'])
RightAscension = repr(label['Caminfo']['Geometry']['RightAscension'])
Declination = repr(label['Caminfo']['Geometry']['Declination'])
PhaseAngle = repr(label['Caminfo']['Geometry']['PhaseAngle'])
EmissionAngle = repr(label['Caminfo']['Geometry']['EmissionAngle'])
IncidenceAngle = repr(label['Caminfo']['Geometry']['IncidenceAngle'])
NorthAzimuth = repr(label['Caminfo']['Geometry']['NorthAzimuth'])
OffNadir = repr(label['Caminfo']['Geometry']['OffNadir'])
SolarLongitude = repr(label['Caminfo']['Geometry']['SolarLongitude'])
LocalTime = repr(label['Caminfo']['Geometry']['LocalTime'])
TargetCenterDistance = repr(label['Caminfo']['Geometry']['TargetCenterDistance'])
SlantDistance = repr(label['Caminfo']['Geometry']['SlantDistance'])
SampleResolution = repr(label['Caminfo']['Geometry']['SampleResolution'])
LineResolution = repr(label['Caminfo']['Geometry']['LineResolution'])
PixelResolution = repr(label['Caminfo']['Geometry']['PixelResolution'])
MeanGroundResolution = repr(label['Caminfo']['Geometry']['MeanGroundResolution'])
SubSolarAzimuth = repr(label['Caminfo']['Geometry']['SubSolarAzimuth'])
SubSolarGroundAzimuth = repr(label['Caminfo']['Geometry']['SubSolarGroundAzimuth'])
SubSolarLatitude = repr(label['Caminfo']['Geometry']['SubSolarLatitude'])
SubSolarLongitude = repr(label['Caminfo']['Geometry']['SubSolarLongitude'])
SubSpacecraftAzimuth = repr(label['Caminfo']['Geometry']['SubSpacecraftAzimuth'])
SubSpacecraftLatitude = repr(label['Caminfo']['Geometry']['SubSpacecraftLatitude'])
SubSpacecraftLongitude = repr(label['Caminfo']['Geometry']['SubSpacecraftLongitude'])
ParallaxX = repr(label['Caminfo']['Geometry']['ParallaxX'])
ParallaxY = repr(label['Caminfo']['Geometry']['ParallaxY'])
ShadowX = repr(label['Caminfo']['Geometry']['ShadowX'])
ShadowY = repr(label['Caminfo']['Geometry']['ShadowY'])

#Get Polygon section
CentroidLine = repr(label['Caminfo']['Polygon']['CentroidLine'])
CentroidSample = repr(label['Caminfo']['Polygon']['CentroidSample'])
CentroidLatitude = repr(label['Caminfo']['Polygon']['CentroidLatitude'])
CentroidLongitude = repr(label['Caminfo']['Polygon']['CentroidLongitude'])
CentroidRadius = label['Caminfo']['Polygon']['CentroidRadius']
CentroidRadius = repr(CentroidRadius[0])
SurfaceArea = label['Caminfo']['Polygon']['SurfaceArea']
SurfaceArea = repr(SurfaceArea[0])
GlobalCoverage = label['Caminfo']['Polygon']['GlobalCoverage']
GlobalCoverage = repr(GlobalCoverage[0])
GisFootprint =  label['Caminfo']['Polygon']['GisFootprint']

#Create CSV with fieldname and a single data row
#fields = ("Filename,StartTime,EndTime,CenterLine,CenterSample,CenterLatitude,"+
fields = ("Filename,CenterLine,CenterSample,CenterLatitude,"+
         "CenterLongitude,CenterRadius,RightAscension,Declination,PhaseAngle,"+
         "EmissionAngle,IncidenceAngle,NorthAzimuth,OffNadir,SolarLongitude,"+
         "LocalTime,TargetCenterDistance,SlantDistance,SampleResolution,"+
         "LineResolution,PixelResolution,MeanGroundResolution,SubSolarAzimuth,"+
         "SubSolarGroundAzimuth,SubSolarLatitude,SubSolarLongitude,"+
         "SubSpacecraftAzimuth,SubSpacecraftLatitude,SubSpacecraftLongitude,"+
         "ParallaxX,ParallaxY,ShadowX,ShadowY,CentroidLine,CentroidSample,"+
         "CentroidLatitude,CentroidLongitude,CentroidRadius,SurfaceArea,"+
         "GlobalCoverage,GisFootprint")
#row = Filename+","+StartTime+","+EndTime+","+CenterLine+","+CenterSample+","+CenterLatitude+ \
row = Filename+","+CenterLine+","+CenterSample+","+CenterLatitude+ \
      ","+CenterLongitude+","+CenterRadius+","+RightAscension+","+Declination+","+PhaseAngle+ \
      ","+EmissionAngle+","+IncidenceAngle+","+NorthAzimuth+","+OffNadir+","+SolarLongitude+ \
      ","+LocalTime+","+TargetCenterDistance+","+SlantDistance+","+SampleResolution+ \
      ","+LineResolution+","+PixelResolution+","+MeanGroundResolution+","+SubSolarAzimuth+ \
      ","+SubSolarGroundAzimuth+","+SubSolarLatitude+","+SubSolarLongitude+ \
      ","+SubSpacecraftAzimuth+","+SubSpacecraftLatitude+","+SubSpacecraftLongitude+ \
      ","+ParallaxX+","+ParallaxY+","+ShadowX+","+ShadowY+","+CentroidLine+","+CentroidSample+ \
      ","+CentroidLatitude+","+CentroidLongitude+","+CentroidRadius+","+SurfaceArea+ \
      ","+str(GlobalCoverage)+",\""+GisFootprint+"\""
#print row
target = open(outputCsv, 'w')
target.write(fields)
target.write('\n')
target.write(row)
target.write('\n')
target.close()

###########################
#Create CSVT (type mapping for fields)
#fieldMapping = ('"String","String","String","Real","Real","Real",'+
fieldMapping = ('"String","Real","Real","Real",'+
               '"Real","Real","Real","Real","Real",'+
               '"Real","Real","Real","Real","Real",'+
               '"Real","Real","Real","Real",'+
               '"Real","Real","Real","Real",'+
               '"Real","Real","Real",'+
               '"Real","Real","Real",'+
               '"Real","Real","Real","Real","Real","Real",'+
               '"Real","Real","Real","Real",'+
               '"Real","String"')
target = open(outputCsvt, 'w')
target.write(fieldMapping)
target.write('\n')
target.close()

###########################
#Create an VRT layer
target = open(outputVRT, 'w')
target.write('<OGRVRTDataSource>\n')
target.write('  <OGRVRTLayer name="%s">\n' % (inputNoExt))
target.write('    <SrcDataSource>%s</SrcDataSource>\n' % (outputCsv))
target.write('    <GeometryType>wkbPolygon</GeometryType>\n')
#target.write('    <LayerSRS>GEOGCS["Enceladus 2009",DATUM["D_Enceladus_2009",SPHEROID["Enceladus_2009_IAU_IAG",252100.0,0.0]],PRIMEM["Reference_Meridian",0],UNIT["Decimal_Degree",0.0174532925199433],AUTHORITY["IAU2009","60200"]]</LayerSRS>

#Default projection to help define it is degrees. User should send *.prj
target.write('    <LayerSRS>WGS84</LayerSRS>\n')
target.write('    <GeometryField encoding="WKT" field="GisFootprint"/>\n')
target.write('  </OGRVRTLayer>\n')
target.write('</OGRVRTDataSource>\n')
target.close()

while os.path.isfile(outputVRT) == False:
    time.sleep(10)
    print "sleeping"

###########################
#convert VRT using ogr2ogr
if projection is None:
  print 'No projection sent, defaulting to WGS84 (degrees)'
  #os.system('ogr2ogr -f "ESRI Shapefile" -overwrite -skipfailures -oo AUTODETECT_TYPE=YES -oo HEADERS=YES %s %s' % (outputShp,outputVRT))  
  os.system('ogr2ogr -f "ESRI Shapefile" -overwrite -skipfailures %s %s' % (outputShp,outputVRT))  
else:
  #os.system('ogr2ogr -f "ESRI Shapefile" -a_srs %s -overwrite -skipfailures -oo AUTODETECT_TYPE=YES -oo HEADERS=YES %s %s' % (projection,outputShp,outputVRT))  
  os.system('ogr2ogr -f "ESRI Shapefile" -a_srs %s -overwrite -skipfailures %s %s' % (projection,outputShp,outputVRT))  

if os.path.isfile(outputShp):
  print 'shapefile created: %s.\n  Note: intermediate files *.pvl, *.csv, *.csvt, and *.vrt can be deleted.' % (outputShp)
else:
  print 'shapefile not created'


