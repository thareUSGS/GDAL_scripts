#!/usr/bin/env python
#/******************************************************************************
# * $Id$
# *
# * Project:  GDAL/OGR Utilities
# * Purpose:  GDAL raster to partial FDGC metadata XML file.
# *
# * Author:   Trent Hare, <thare at usgs dot gov>
# * Date:     Oct 10, 2011
# * version:  0.2 (proof of concept - still not well tested!)
# *
# * Port from gdalinfo.py whose author is Even Rouault and Frank Warmerdam
# *
# ******************************************************************************
# * Copyright (c) 2010, Even Rouault
# * Copyright (c) 1998, Frank Warmerdam
# *
# * Permission is hereby granted, free of charge, to any person obtaining a
# * copy of this software and associated documentation files (the "Software"),
# * to deal in the Software without restriction, including without limitation
# * the rights to use, copy, modify, merge, publish, distribute, sublicense,
# * and/or sell copies of the Software, and to permit persons to whom the
# * Software is furnished to do so, subject to the following conditions:
# *
# * The above copyright notice and this permission notice shall be included
# * in all copies or substantial portions of the Software.
# *
# * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# * DEALINGS IN THE SOFTWARE.
# ****************************************************************************/

import sys
import math
from time import strftime
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import gdal
    import osr

try:
  from lxml import etree
  #print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")


#/************************************************************************/
#/*                               Usage()                                */
#/************************************************************************/

def Usage(theApp):
    print( '\nUsage: gdal2metadata in_Geo.tif in_FGDCtemplate.xml output.xml') # % theApp)
    print( '   Optional: to print out image information also send -debug')
    print( 'Usage: gdal2metadata -debug in_Geo.tif in_FGDCtemplate.xml output.xml\n') # % theApp)
    print( 'Note: Currently this routine only supports FGDC version CSDGM - FGDC-STD-001-1998\n')
    sys.exit(1)


def EQUAL(a, b):
    return a.lower() == b.lower()


#/************************************************************************/
#/*                                main()                                */
#/************************************************************************/

def main( argv = None ):

    bComputeMinMax = False
    bSample = False
    bShowGCPs = True
    bShowMetadata = True
    bShowRAT=False
    debug = False
    bStats = False
    bApproxStats = True
    bShowColorTable = True
    bComputeChecksum = False
    bReportHistograms = False
    pszFilename = None
    papszExtraMDDomains = [ ]
    pszProjection = None
    hTransform = None
    bShowFileList = True
    dst_xml = None
    template_xml = None
    bands = 1
    iOverview = None

    if argv is None:
        argv = sys.argv

    argv = gdal.GeneralCmdLineProcessor( argv )

    if argv is None:
        return 1

    nArgc = len(argv)

#/* -------------------------------------------------------------------- */
#/*      Parse arguments.                                                */
#/* -------------------------------------------------------------------- */
    i = 1
    while i < nArgc:

        if EQUAL(argv[i], "--utility_version"):
            print(("%s is running against GDAL %s" %
                   (argv[0], gdal.VersionInfo("RELEASE_NAME"))))
            return 0
        elif EQUAL(argv[i], "-debug"):
            debug = True
        elif EQUAL(argv[i], "-mm"):
            bComputeMinMax = True
        elif EQUAL(argv[i], "-hist"):
            bReportHistograms = True
        elif EQUAL(argv[i], "-stats"):
            bStats = True
            bApproxStats = False
        elif EQUAL(argv[i], "-approx_stats"):
            bStats = True
            bApproxStats = True
        elif EQUAL(argv[i], "-sample"):
            bSample = True
        elif EQUAL(argv[i], "-checksum"):
            bComputeChecksum = True
        elif EQUAL(argv[i], "-nogcp"):
            bShowGCPs = False
        elif EQUAL(argv[i], "-nomd"):
            bShowMetadata = False
        elif EQUAL(argv[i], "-norat"):
            bShowRAT = False
        elif EQUAL(argv[i], "-noct"):
            bShowColorTable = False
        elif EQUAL(argv[i], "-mdd") and i < nArgc-1:
            i = i + 1
            papszExtraMDDomains.append( argv[i] )
        elif EQUAL(argv[i], "-nofl"):
            bShowFileList = False
        elif argv[i][0] == '-':
            return Usage(argv[0])
        elif pszFilename is None:
            pszFilename = argv[i]
        elif template_xml is None:
            template_xml = argv[i]
        elif dst_xml is None:
            dst_xml = argv[i]
        else:
            return Usage(argv[0])
        i = i + 1

    if pszFilename is None:
        return Usage(argv[0])
    if template_xml is None:
        return Usage(argv[0])
    if dst_xml is None:
        return Usage(argv[0])

#/* -------------------------------------------------------------------- */
#/*      Open GDAL dataset.                                              */
#/* -------------------------------------------------------------------- */
    hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly )

    if hDataset is None:
        print(("gdalinfo failed - unable to open '%s'." % pszFilename ))
        sys.exit(1)

#/* -------------------------------------------------------------------- */
#/*     load XML template file (generally fgdc-template.xml)             */
#/* -------------------------------------------------------------------- */
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(template_xml, parser)

    for lworkcit in tree.getiterator('lworkcit'):
        for citeinfo in lworkcit.getiterator('citeinfo'):
            title = citeinfo.find('title')
            if title is None:        
                title = etree.SubElement(citeinfo, 'title')
            title.text = pszFilename

#/* -------------------------------------------------------------------- */
#/*      Report general info.                                            */
#/* -------------------------------------------------------------------- */
    hDriver = hDataset.GetDriver();
    if debug:
        print(( "Driver: %s/%s" % ( \
                hDriver.ShortName, \
                hDriver.LongName )))

    papszFileList = hDataset.GetFileList();
    if papszFileList is None or len(papszFileList) == 0:
        print( "Files: none associated" )
    else:
        if debug:
            print(( "Files: %s" % papszFileList[0] ))
            if bShowFileList:
                for i in range(1, len(papszFileList)):
                    print(( "       %s" % papszFileList[i] ))

    if debug:
        print(( "Size is %d, %d" % (hDataset.RasterXSize, hDataset.RasterYSize)))

#/* -------------------------------------------------------------------- */
#/*      Report projection.                                              */
#/* -------------------------------------------------------------------- */
    pszProjection = hDataset.GetProjectionRef()
    if pszProjection is not None:

        hSRS = osr.SpatialReference()
        if hSRS.ImportFromWkt(pszProjection ) == gdal.CE_None:
            pszPrettyWkt = hSRS.ExportToPrettyWkt(False)

            #print( "Coordinate System is:\n%s" % pszPrettyWkt )
            mapProjection = "None"
            #Extract projection information
            target = hSRS.GetAttrValue("DATUM",0).replace("D_","").replace("_2000","")
            semiMajor = hSRS.GetSemiMajor() #/ 1000.0
            semiMinor = hSRS.GetSemiMinor() #/ 1000.0
            invFlat = hSRS.GetInvFlattening()
            # the USGS tool MP doesn't like 0 for the invFlat so we are putting a giant number to represent a sphere
            if (invFlat < 0.1):
               invFlat = 1.0e+10

            if (pszProjection[0:6] == "GEOGCS"):
                mapProjection = "SIMPLE_CYLINDRICAL"
                centLat = 0
                centLon = 0
            if (pszProjection[0:6] == "PROJCS"):
                mapProjection = hSRS.GetAttrValue("PROJECTION",0)

                for horizsys in tree.getiterator('horizsys'):
                    horizsys.clear()
                    planar = etree.SubElement(horizsys, 'planar')
                    mapproj = etree.SubElement(planar, 'mapproj')
                    mapprojn = etree.SubElement(mapproj, 'mapprojn')

                if EQUAL(mapProjection,"Equirectangular"):
                    #for mapprojn in tree.getiterator('mapprojn'):
                    mapprojn.text = "Equirectangular"
                    centLat = None
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    if centLat == None:
                        centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                    equirect = etree.SubElement(mapproj, 'equirect')
                    #for equirect in tree.getiterator('equirect'):
                    stdparll = etree.SubElement(equirect, 'stdparll')
                    #for stdparll in equirect.getiterator('stdparll'):
                    stdparll.text = str(centLat)
                    #for longcm in equirect.getiterator('longcm'):
                    longcm = etree.SubElement(equirect, 'longcm')
                    longcm.text = str(centLon)
                    #for feast in equirect.getiterator('feast'):
                    feast = etree.SubElement(equirect, 'feast')
                    feast.text = str(hSRS.GetProjParm('false_easting'))
                    #for fnorth in equirect.getiterator('fnorth'):
                    fnorth = etree.SubElement(equirect, 'fnorth')
                    fnorth.text = str(hSRS.GetProjParm('false_northing'))
                            
                if EQUAL(mapProjection,"Mercator"):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Mercator"
                    centLat = None
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    if centLat == None:
                        centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')
                    scale = hSRS.GetProjParm('scale_factor')
                    for merc in tree.getiterator('transmer'):
                        for stdparll in merc.getiterator('stdparll'):
                            stdparll.text = str(centLat)
                        for longcm in merc.getiterator('longcm'):
                            longcm.text = str(centLon)
                        for sfequat in merc.getiterator('sfequat'):
                            sfequat.text = str(scale)
                        for feast in merc.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in merc.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))
                
                if EQUAL(mapProjection,"Orthographic "):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Orthographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin ')
                    centLon = hSRS.GetProjParm('central_meridian')
                    for orthogr in tree.getiterator('orthogr'):
                        for stdparll in orthogr.getiterator('stdparll'):
                            stdparll.text = str(centLat)
                        for longcm in orthogr.getiterator('longcm'):
                            longcm.text = str(centLon)
                        for feast in orthogr.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in orthogr.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))

                if EQUAL(mapProjection,"Stereographic"):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Stereographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                    for stereo in tree.getiterator('stereo'):
                        for latprjc in stereo.getiterator('latprjc'):
                            latprjc.text = str(centLat)
                        for longpc in stereo.getiterator('longpc'):
                            longpc.text = str(centLon)
                        for feast in stereo.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in stereo.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))

                if EQUAL(mapProjection,"Sinusoidal"):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Sinusoidal"
                    centLon = None
                    centLon = hSRS.GetProjParm('longitude_of_center')
                    if centLon == None:
                        centLon = hSRS.GetProjParm('central_meridian')
                    for sinusoid in tree.getiterator('sinusoid'):
                        for longcm in sinusoid.getiterator('longcm'):
                            longcm.text = str(centLon)
                        for feast in sinusoid.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in sinusoid.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))

                if EQUAL(mapProjection,"Robinson"):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Robinson"
                    centLon = None
                    centLon = hSRS.GetProjParm('longitude_of_center')
                    if centLon == None:
                        centLon = hSRS.GetProjParm('central_meridian')
                    for robinson in tree.getiterator('robinson'):
                        for longpc in robinson.getiterator('longpc'):
                            longpc.text = str(centLon)
                        for feast in robinson.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in robinson.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))

                if (EQUAL(mapProjection,"Polar_Stereographic") or EQUAL(mapProjection,"Stereographic_North_Pole") or EQUAL(mapProjection,"Stereographic_South_Pole")):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Polar Stereographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                    scale = hSRS.GetProjParm('scale_factor')
                    for polarst in tree.getiterator('polarst'):
                        for stdparll in polarst.getiterator('stdparll'):
                            stdparll.text = str(centLat)
                        for svlong in polarst.getiterator('svlong'):
                            svlong.text = str(centLon)
                        for sfprjorg in polarst.getiterator('sfprjorg'):
                            sfprjorg.text = str(scale)
                        for feast in polarst.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in polarst.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))

                if EQUAL(mapProjection,"Transverse_Mercator"):
                    for mapprojn in tree.getiterator('mapprojn'):
                        mapprojn.text = "Transverse Mercator"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                    scale = hSRS.GetProjParm('scale_factor')
                    for transmer in tree.getiterator('transmer'):
                        for latprjo in transmer.getiterator('latprjo'):
                            latprjo.text = str(centLat)
                        for longcm in transmer.getiterator('longcm'):
                            longcm.text = str(centLon)
                        for sfctrmer in transmer.getiterator('sfctrmer'):
                            sfctrmer.text = str(scale)
                        for feast in transmer.getiterator('feast'):
                            feast.text = str(hSRS.GetProjParm('false_easting'))
                        for fnorth in transmer.getiterator('fnorth'):
                            fnorth.text = str(hSRS.GetProjParm('false_northing'))
                

                #Create cellsize block for all projections
                planci = etree.SubElement(planar, 'planci')
                plance = etree.SubElement(planci, 'plance')
                plance.text = 'row and column'
                coordrep = etree.SubElement(planci, 'coordrep')
                absres = etree.SubElement(coordrep, 'absres')
                ordres = etree.SubElement(coordrep, 'ordres')
                plandu = etree.SubElement(planci, 'plandu')

            if debug:
                print(( "Coordinate System is:\n%s" % pszPrettyWkt ))
        else:
            print( "Warning - Can't parse this type of projection\n" )
            print(( "Coordinate System is `%s'" % pszProjection ))
            sys.exit(1)
    else:
        print( "Warning - No Coordinate System defined:\n" )
        sys.exit(1)
        
#/* -------------------------------------------------------------------- */
#/*      Report Geotransform.                                            */
#/* -------------------------------------------------------------------- */
    adfGeoTransform = hDataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:

        if adfGeoTransform[2] == 0.0 and adfGeoTransform[4] == 0.0:
            if debug:
                print(( "Origin = (%.15f,%.15f)" % ( \
                        adfGeoTransform[0], adfGeoTransform[3] )))

                print(( "Pixel Size = (%.15f,%.15f)" % ( \
                        adfGeoTransform[1], adfGeoTransform[5] )))

        else:
            if debug:
                print(( "GeoTransform =\n" \
                        "  %.16g, %.16g, %.16g\n" \
                        "  %.16g, %.16g, %.16g" % ( \
                        adfGeoTransform[0], \
                        adfGeoTransform[1], \
                        adfGeoTransform[2], \
                        adfGeoTransform[3], \
                        adfGeoTransform[4], \
                        adfGeoTransform[5] )))

        if (pszProjection[0:6] == "GEOGCS"):
            #convert degrees/pixel to km/pixel 
             mapres = 1 / adfGeoTransform[1]
             lonres = adfGeoTransform[1]
             latres = adfGeoTransform[5]
             kmres = adfGeoTransform[1] * (semiMajor * math.pi / 180.0)
        else:
            #convert m/pixel to pixel/degree
             mapres = 1 / (adfGeoTransform[1] / (semiMajor * 1000.0 * math.pi / 180.0))
             lonres = adfGeoTransform[1] / (semiMajor * 1000.0 * math.pi / 180.0)
             latres = adfGeoTransform[5] / (semiMajor * 1000.0 * math.pi / 180.0)
             xres = adfGeoTransform[1]
             yres = adfGeoTransform[5]
             kmres = adfGeoTransform[1] / 1000.0

#/* -------------------------------------------------------------------- */
#/*      Report GCPs.                                                    */
#/* -------------------------------------------------------------------- */
    if bShowGCPs and hDataset.GetGCPCount() > 0:

        pszProjection = hDataset.GetGCPProjection()
        if pszProjection is not None:

            hSRS = osr.SpatialReference()
            if hSRS.ImportFromWkt(pszProjection ) == gdal.CE_None:
                pszPrettyWkt = hSRS.ExportToPrettyWkt(False)
                if debug:
                    print(( "GCP Projection = \n%s" % pszPrettyWkt ))

            else:
                if debug:
                    print(( "GCP Projection = %s" % \
                            pszProjection ))

        gcps = hDataset.GetGCPs()
        i = 0
        for gcp in gcps:

            if debug:
                print(( "GCP[%3d]: Id=%s, Info=%s\n" \
                        "          (%.15g,%.15g) -> (%.15g,%.15g,%.15g)" % ( \
                        i, gcp.Id, gcp.Info, \
                        gcp.GCPPixel, gcp.GCPLine, \
                        gcp.GCPX, gcp.GCPY, gcp.GCPZ )))
            i = i + 1

#/* -------------------------------------------------------------------- */
#/*      Report metadata.                                                */
#/* -------------------------------------------------------------------- */
    if debug:
        if bShowMetadata:
            papszMetadata = hDataset.GetMetadata_List()
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "Metadata:" )
            for metadata in papszMetadata:
                print(( "  %s" % metadata ))

        if bShowMetadata:
            for extra_domain in papszExtraMDDomains:
                papszMetadata = hDataset.GetMetadata_List(extra_domain)
                if papszMetadata is not None and len(papszMetadata) > 0 :
                    print(( "Metadata (%s):" % extra_domain))
                    for metadata in papszMetadata:
                      print(( "  %s" % metadata ))

#/* -------------------------------------------------------------------- */
#/*      Report "IMAGE_STRUCTURE" metadata.                              */
#/* -------------------------------------------------------------------- */
        if bShowMetadata:
            papszMetadata = hDataset.GetMetadata_List("IMAGE_STRUCTURE")
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "Image Structure Metadata:" )
            for metadata in papszMetadata:
                print(( "  %s" % metadata ))

#/* -------------------------------------------------------------------- */
#/*      Report subdatasets.                                             */
#/* -------------------------------------------------------------------- */
        papszMetadata = hDataset.GetMetadata_List("SUBDATASETS")
        if papszMetadata is not None and len(papszMetadata) > 0 :
            print( "Subdatasets:" )
            for metadata in papszMetadata:
                print(( "  %s" % metadata ))

#/* -------------------------------------------------------------------- */
#/*      Report geolocation.                                             */
#/* -------------------------------------------------------------------- */
        if bShowMetadata:
            papszMetadata = hDataset.GetMetadata_List("GEOLOCATION")
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "Geolocation:" )
            for metadata in papszMetadata:
                print(( "  %s" % metadata ))

#/* -------------------------------------------------------------------- */
#/*      Report RPCs                                                     */
#/* -------------------------------------------------------------------- */
        if bShowMetadata:
            papszMetadata = hDataset.GetMetadata_List("RPC")
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "RPC Metadata:" )
            for metadata in papszMetadata:
                print(( "  %s" % metadata ))

#/* -------------------------------------------------------------------- */
#/*      Setup projected to lat/long transform if appropriate.           */
#/* -------------------------------------------------------------------- */
    if pszProjection is not None and len(pszProjection) > 0:
        hProj = osr.SpatialReference( pszProjection )
        if hProj is not None:
            hLatLong = hProj.CloneGeogCS()

        if hLatLong is not None:
            gdal.PushErrorHandler( 'CPLQuietErrorHandler' )
            hTransform = osr.CoordinateTransformation( hProj, hLatLong )
            gdal.PopErrorHandler()
            if gdal.GetLastErrorMsg().find( 'Unable to load PROJ.4 library' ) != -1:
                hTransform = None

#/* -------------------------------------------------------------------- */
#/*      Report corners.                                                 */
#/* -------------------------------------------------------------------- */
    if debug:
        print( "Corner Coordinates:" )
        GDALInfoReportCorner( hDataset, hTransform, "Upper Left", \
                              0.0, 0.0 );
        GDALInfoReportCorner( hDataset, hTransform, "Lower Left", \
                              0.0, hDataset.RasterYSize);
        GDALInfoReportCorner( hDataset, hTransform, "Upper Right", \
                              hDataset.RasterXSize, 0.0 );
        GDALInfoReportCorner( hDataset, hTransform, "Lower Right", \
                              hDataset.RasterXSize, \
                              hDataset.RasterYSize );
        GDALInfoReportCorner( hDataset, hTransform, "Center", \
                              hDataset.RasterXSize/2.0, \
                              hDataset.RasterYSize/2.0 );

    #Get bounds
    ulx = GDALGetLon( hDataset, hTransform, 0.0, 0.0 );
    uly = GDALGetLat( hDataset, hTransform, 0.0, 0.0 );
    lrx = GDALGetLon( hDataset, hTransform, hDataset.RasterXSize, \
                          hDataset.RasterYSize );
    lry = GDALGetLat( hDataset, hTransform, hDataset.RasterXSize, \
                          hDataset.RasterYSize );
       
    #FGDC metadata requires -180 to 180 to pass validation (not 0 to 360).                   
    if (lrx > 179.99):
       lrx = lrx - 360   
    if (ulx > 179.99):
       ulx = ulx - 360

#/* ==================================================================== */
#/*      Loop over bands.                                                */
#/* ==================================================================== */
    if debug:
        bands = hDataset.RasterCount
        for iBand in range(hDataset.RasterCount):

                hBand = hDataset.GetRasterBand(iBand+1 )

                #if( bSample )
                #{
                #    float afSample[10000];
                #    int   nCount;
                #
                #    nCount = GDALGetRandomRasterSample( hBand, 10000, afSample );
                #    print( "Got %d samples.\n", nCount );
                #}

                (nBlockXSize, nBlockYSize) = hBand.GetBlockSize()
                print(( "Band %d Block=%dx%d Type=%s, ColorInterp=%s" % ( iBand+1, \
                                nBlockXSize, nBlockYSize, \
                                gdal.GetDataTypeName(hBand.DataType), \
                                gdal.GetColorInterpretationName( \
                                        hBand.GetRasterColorInterpretation()) )))

                if hBand.GetDescription() is not None \
                        and len(hBand.GetDescription()) > 0 :
                        print(( "  Description = %s" % hBand.GetDescription() ))

                dfMin = hBand.GetMinimum()
                dfMax = hBand.GetMaximum()
                if dfMin is not None or dfMax is not None or bComputeMinMax:

                        line =  "  "
                        if dfMin is not None:
                                line = line + ("Min=%.3f " % dfMin)
                        if dfMax is not None:
                                line = line + ("Max=%.3f " % dfMax)

                        if bComputeMinMax:
                                gdal.ErrorReset()
                                adfCMinMax = hBand.ComputeRasterMinMax(False)
                                if gdal.GetLastErrorType() == gdal.CE_None:
                                  line = line + ( "  Computed Min/Max=%.3f,%.3f" % ( \
                                                  adfCMinMax[0], adfCMinMax[1] ))

                        print( line )

                stats = hBand.GetStatistics( bApproxStats, bStats)
                # Dirty hack to recognize if stats are valid. If invalid, the returned
                # stddev is negative
                if stats[3] >= 0.0:
                        print(( "  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                                        stats[0], stats[1], stats[2], stats[3] )))

                if bReportHistograms:

                        hist = hBand.GetDefaultHistogram(force = True, callback = gdal.TermProgress)
                        if hist is not None:
                                dfMin = hist[0]
                                dfMax = hist[1]
                                nBucketCount = hist[2]
                                panHistogram = hist[3]

                                print(( "  %d buckets from %g to %g:" % ( \
                                                nBucketCount, dfMin, dfMax )))
                                line = '  '
                                for bucket in panHistogram:
                                        line = line + ("%d " % bucket)

                                print(line)

                if bComputeChecksum:
                        print(( "  Checksum=%d" % hBand.Checksum()))

                dfNoData = hBand.GetNoDataValue()
                if dfNoData is not None:
                        if dfNoData != dfNoData:
                                print( "  NoData Value=nan" )
                        else:
                                print(( "  NoData Value=%.18g" % dfNoData ))

                if hBand.GetOverviewCount() > 0:

                        line = "  Overviews: "
                        for iOverview in range(hBand.GetOverviewCount()):

                                if iOverview != 0 :
                                        line = line +  ", "

                                hOverview = hBand.GetOverview( iOverview );
                                if hOverview is not None:

                                        line = line + ( "%dx%d" % (hOverview.XSize, hOverview.YSize))

                                        pszResampling = \
                                                hOverview.GetMetadataItem( "RESAMPLING", "" )

                                        if pszResampling is not None \
                                           and len(pszResampling) >= 12 \
                                           and EQUAL(pszResampling[0:12],"AVERAGE_BIT2"):
                                                line = line + "*"

                                else:
                                        line = line + "(null)"

                        print(line)

                        if bComputeChecksum:

                                line = "  Overviews checksum: "
                                for iOverview in range(hBand.GetOverviewCount()):

                                        if iOverview != 0:
                                                line = line +  ", "

                                        hOverview = hBand.GetOverview( iOverview );
                                        if hOverview is not None:
                                                line = line + ( "%d" % hOverview.Checksum())
                                        else:
                                                line = line + "(null)"
                                print(line)

                if hBand.HasArbitraryOverviews():
                        print( "  Overviews: arbitrary" )

                nMaskFlags = hBand.GetMaskFlags()
                if (nMaskFlags & (gdal.GMF_NODATA|gdal.GMF_ALL_VALID)) == 0:

                        hMaskBand = hBand.GetMaskBand()

                        line = "  Mask Flags: "
                        if (nMaskFlags & gdal.GMF_PER_DATASET) != 0:
                                line = line + "PER_DATASET "
                        if (nMaskFlags & gdal.GMF_ALPHA) != 0:
                                line = line + "ALPHA "
                        if (nMaskFlags & gdal.GMF_NODATA) != 0:
                                line = line + "NODATA "
                        if (nMaskFlags & gdal.GMF_ALL_VALID) != 0:
                                line = line + "ALL_VALID "
                        print(line)

                        if hMaskBand is not None and \
                                hMaskBand.GetOverviewCount() > 0:

                                line = "  Overviews of mask band: "
                                for iOverview in range(hMaskBand.GetOverviewCount()):

                                        if iOverview != 0:
                                                line = line +  ", "

                                        hOverview = hMaskBand.GetOverview( iOverview );
                                        if hOverview is not None:
                                                line = line + ( "%d" % hOverview.Checksum())
                                        else:
                                                line = line + "(null)"

                if len(hBand.GetUnitType()) > 0:
                        print(( "  Unit Type: %s" % hBand.GetUnitType()))

                papszCategories = hBand.GetRasterCategoryNames()
                if papszCategories is not None:

                        print( "  Categories:" );
                        i = 0
                        for category in papszCategories:
                                print(( "    %3d: %s" % (i, category) ))
                                i = i + 1

                if hBand.GetScale() != 1.0 or hBand.GetOffset() != 0.0:
                        print(( "  Offset: %.15g,   Scale:%.15g" % \
                                                ( hBand.GetOffset(), hBand.GetScale())))

                if bShowMetadata:
                        papszMetadata = hBand.GetMetadata_List()
                else:
                        papszMetadata = None
                if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
                        print( "  Metadata:" )
                        for metadata in papszMetadata:
                                print(( "    %s" % metadata ))


                if bShowMetadata:
                        papszMetadata = hBand.GetMetadata_List("IMAGE_STRUCTURE")
                else:
                        papszMetadata = None
                if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
                        print( "  Image Structure Metadata:" )
                        for metadata in papszMetadata:
                                print(( "    %s" % metadata ))


                hTable = hBand.GetRasterColorTable()
                if hBand.GetRasterColorInterpretation() == gdal.GCI_PaletteIndex  \
                        and hTable is not None:

                        print(( "  Color Table (%s with %d entries)" % (\
                                        gdal.GetPaletteInterpretationName( \
                                                hTable.GetPaletteInterpretation(  )), \
                                        hTable.GetCount() )))

                        if bShowColorTable:

                                for i in range(hTable.GetCount()):
                                        sEntry = hTable.GetColorEntry(i)
                                        print(( "  %3d: %d,%d,%d,%d" % ( \
                                                        i, \
                                                        sEntry[0],\
                                                        sEntry[1],\
                                                        sEntry[2],\
                                                        sEntry[3] )))

                if bShowRAT:
                        hRAT = hBand.GetDefaultRAT()

            #GDALRATDumpReadable( hRAT, None );

                if iOverview is not None:
                    hOverview = hBand.GetOverview( iOverview );
                    if hOverview is not None:
                        line = line + ( "%d" % hOverview.Checksum())
                    else:
                        line = line + "(null)"
                    print(line)

        if hBand.HasArbitraryOverviews():
            print( "  Overviews: arbitrary" )

        nMaskFlags = hBand.GetMaskFlags()
        if (nMaskFlags & (gdal.GMF_NODATA|gdal.GMF_ALL_VALID)) == 0:

            hMaskBand = hBand.GetMaskBand()

            line = "  Mask Flags: "
            if (nMaskFlags & gdal.GMF_PER_DATASET) != 0:
                line = line + "PER_DATASET "
            if (nMaskFlags & gdal.GMF_ALPHA) != 0:
                line = line + "ALPHA "
            if (nMaskFlags & gdal.GMF_NODATA) != 0:
                line = line + "NODATA "
            if (nMaskFlags & gdal.GMF_ALL_VALID) != 0:
                line = line + "ALL_VALID "
            print(line)

            if hMaskBand is not None and \
                hMaskBand.GetOverviewCount() > 0:

                line = "  Overviews of mask band: "
                for iOverview in range(hMaskBand.GetOverviewCount()):

                    if iOverview != 0:
                        line = line +  ", "

                    hOverview = hMaskBand.GetOverview( iOverview );
                    if hOverview is not None:
                        line = line + ( "%d" % hOverview.Checksum())
                    else:
                        line = line + "(null)"

        if len(hBand.GetUnitType()) > 0:
            print(( "  Unit Type: %s" % hBand.GetUnitType()))

        papszCategories = hBand.GetRasterCategoryNames()
        if papszCategories is not None:

            print( "  Categories:" );
            i = 0
            for category in papszCategories:
                print(( "    %3d: %s" % (i, category) ))
                i = i + 1

        if hBand.GetScale() != 1.0 or hBand.GetOffset() != 0.0:
            print(( "  Offset: %.15g,   Scale:%.15g" % \
                        ( hBand.GetOffset(), hBand.GetScale())))

        if bShowMetadata:
            papszMetadata = hBand.GetMetadata_List()
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "  Metadata:" )
            for metadata in papszMetadata:
                print(( "    %s" % metadata ))


        if bShowMetadata:
            papszMetadata = hBand.GetMetadata_List("IMAGE_STRUCTURE")
        else:
            papszMetadata = None
        if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
            print( "  Image Structure Metadata:" )
            for metadata in papszMetadata:
                print(( "    %s" % metadata ))


        hTable = hBand.GetRasterColorTable()
        if hBand.GetRasterColorInterpretation() == gdal.GCI_PaletteIndex  \
            and hTable is not None:

            print(( "  Color Table (%s with %d entries)" % (\
                    gdal.GetPaletteInterpretationName( \
                        hTable.GetPaletteInterpretation(  )), \
                    hTable.GetCount() )))

            if bShowColorTable:

                for i in range(hTable.GetCount()):
                    sEntry = hTable.GetColorEntry(i)
                    print(( "  %3d: %d,%d,%d,%d" % ( \
                            i, \
                            sEntry[0],\
                            sEntry[1],\
                            sEntry[2],\
                            sEntry[3] )))

        if bShowRAT:
            hRAT = hBand.GetDefaultRAT()

            #GDALRATDumpReadable( hRAT, None );

#/************************************************************************/
#/*                      WriteXML bits to FGDC template                  */
#/************************************************************************/
    for rasttype in tree.getiterator('rasttype'):
        rasttype.text = "Pixel"
    #~ instrList = pszFilename.split("_")
    hBand = hDataset.GetRasterBand( 1 )
    #~ #get the datatype
    #~ if EQUAL(gdal.GetDataTypeName(hBand.DataType), "Float32"):
        #~ sample_bits = 32
        #~ sample_type = "PC_REAL"
        #~ sample_mask = "2#11111111111111111111111111111111#"
    #~ elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "INT16"):
        #~ sample_bits = 16
        #~ sample_type = "LSB_INTEGER"
        #~ sample_mask = "2#1111111111111111#"
    #~ elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "UINT16"):
        #~ sample_bits = 16
        #~ sample_type = "UNSIGNED_INTEGER"
        #~ sample_mask = "2#1111111111111111#"
    #~ elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "Byte"):
        #~ sample_bits = 8
        #~ sample_type = "UNSIGNED_INTEGER"
        #~ sample_mask = "2#11111111#"
    #~ else:
        #~ print( "  %s: Not supported pixel type" % gdal.GetDataTypeName(hBand.DataType))
        #~ sys.exit(1)

    #~ f.write('PDS_VERSION_ID            = PDS3\n')
    #~ f.write('\n')
    #~ f.write('/* The source image data definition. */\n')
    #~ f.write('FILE_NAME      = \"%s\"\n' % (dst_img))
    #~ f.write('RECORD_TYPE   = FIXED_LENGTH\n')
    #~ f.write('RECORD_BYTES  = %d\n' % (hDataset.RasterYSize))
    #~ f.write('FILE_RECORDS  = %d\n' % ((hDataset.RasterXSize * sample_bits / 8)) )
    #~ #f.write('LABEL_RECORDS = 1\n')
    #~ f.write('^IMAGE        = \"%s\"\n' % (dst_img))
    #~ f.write('\n')
    #~ f.write('/* Identification Information  */\n')
    #~ f.write('DATA_SET_ID               = "%s"\n' % pszFilename.split(".")[0])
    #~ f.write('DATA_SET_NAME             = "%s"\n' % pszFilename.split(".")[0])
    #~ f.write('PRODUCER_INSTITUTION_NAME = "Lunar Mapping and Modeling Project"\n')
    #~ f.write('PRODUCER_ID               = "LMMP_TEAM"\n')
    #~ f.write('PRODUCER_FULL_NAME        = "LMMP TEAM"\n')
    #~ f.write('PRODUCT_ID                = "%s"\n' % pszFilename.split(".")[0])
    #~ if "_v" in pszFilename:
        #~ f.write('PRODUCT_VERSION_ID        = "%s.0"\n' % instrList[-1].split(".")[0].upper())
    #~ else:
        #~ f.write('PRODUCT_VERSION_ID        = "%s"\n' % "V1.0")
    #~ f.write('PRODUCT_TYPE              = "RDR"\n')
    #~ f.write('INSTRUMENT_HOST_NAME      = "%s"\n' % instrList[0])
    #~ f.write('INSTRUMENT_HOST_ID        = "%s"\n' % instrList[0])
    #~ f.write('INSTRUMENT_NAME           = "%s"\n' % instrList[1])
    #~ f.write('INSTRUMENT_ID             = "%s"\n' % instrList[1])
    #~ f.write('TARGET_NAME               = MOON\n')
    for ellips in tree.getiterator('ellips'):
        ellips.text = target
    #~ f.write('MISSION_PHASE_NAME        = "POST MISSION"\n')
    #~ f.write('RATIONALE_DESC            = "Created at the request of NASA\'s Exploration\n')
    #~ f.write('                            Systems Mission Directorate to support future\n')
    #~ f.write('                            human exploration"\n')
    #~ f.write('SOFTWARE_NAME             = "ISIS 3.2.1 | SOCET SET v5.5 (r) BAE Systems\n')
    #~ f.write('                            | GDAL 1.8"\n')
    #~ f.write('\n')
    #~ f.write('/* Time Parameters */\n')
    #~ f.write('START_TIME                   = "N/A"\n')
    #~ f.write('STOP_TIME                    = "N/A"\n')
    #~ f.write('SPACECRAFT_CLOCK_START_COUNT = "N/A"\n')
    #~ f.write('SPACECRAFT_CLOCK_STOP_COUNT  = "N/A"\n')
    #~ f.write('PRODUCT_CREATION_TIME        = %s\n' % strftime("%Y-%m-%dT%H:%M:%S"))   #2011-03-11T22:13:40
    #~ f.write('\n')
    #~ f.write('OBJECT = IMAGE_MAP_PROJECTION\n')
    #~ f.write('    ^DATA_SET_MAP_PROJECTION     = "DSMAP.CAT"\n')
    #~ f.write('    MAP_PROJECTION_TYPE          = \"%s\"\n' % mapProjection)
    #~ f.write('    PROJECTION_LATITUDE_TYPE     = PLANETOCENTRIC\n')
    #~ f.write('    A_AXIS_RADIUS                = %.1f <KM>\n' % semiMajor)
    for semiaxis in tree.getiterator('semiaxis'):
        semiaxis.text = str(semiMajor)
    #~ f.write('    B_AXIS_RADIUS                = %.1f <KM>\n' % semiMajor)
    #~ f.write('    C_AXIS_RADIUS                = %.1f <KM>\n' % semiMinor)
    for denflat in tree.getiterator('denflat'):
        denflat.text = str(invFlat)
    #~ f.write('    COORDINATE_SYSTEM_NAME       = PLANETOCENTRIC\n')
    #~ f.write('    POSITIVE_LONGITUDE_DIRECTION = EAST\n')
    #~ f.write('    KEYWORD_LATITUDE_TYPE        = PLANETOCENTRIC\n')
    #~ f.write('    /* NOTE:  CENTER_LATITUDE and CENTER_LONGITUDE describe the location   */\n')
    #~ f.write('    /* of the center of projection, which is not necessarily equal to the  */\n')
    #~ f.write('    /* location of the center point of the image.                          */\n')
    #~ f.write('    CENTER_LATITUDE              = %5.2f <DEG>\n' % centLat)
    #~ f.write('    CENTER_LONGITUDE             = %5.2f <DEG>\n' % centLon)
    #~ f.write('    LINE_FIRST_PIXEL             = 1\n')
    #~ f.write('    LINE_LAST_PIXEL              = %d\n' % hDataset.RasterYSize)
    #~ f.write('    SAMPLE_FIRST_PIXEL           = 1\n')
    #~ f.write('    SAMPLE_LAST_PIXEL            = %d\n' % hDataset.RasterXSize)
    #~ f.write('    MAP_PROJECTION_ROTATION      = 0.0 <DEG>\n')
    #~ f.write('    MAP_RESOLUTION               = %.4f <PIX/DEG>\n' % mapres )
    if (pszProjection[0:6] == "GEOGCS"):
        for latSize in tree.getiterator('latres'):
            latSize.text = str(latres)
            if debug:
               print('Lat resolution: %s' %(latSize.text))
        for lonSize in tree.getiterator('lonres'):
            lonSize.text = str(lonres)
        for geogunit in tree.getiterator('geogunit'):
            geogunit.text = "Decimal degrees"
    #~ f.write('    MAP_SCALE                    = %.8f <KM/PIXEL>\n' % kmres )
    else:
        for absres in tree.getiterator('absres'): # in meters
            absres.text = str(xres)
            if debug:
               print('X resolution: %s' %(absres.text))
        for ordres in tree.getiterator('ordres'):
            ordres.text = str(abs(yres))
        for plandu in tree.getiterator('plandu'):
            plandu.text = "meters"
    #~ f.write('    MINIMUM_LATITUDE             = %.8f <DEGREE>\n' % lry)
    for southbc in tree.getiterator('southbc'):
        southbc.text = str(lry)
    #~ f.write('    MAXIMUM_LATITUDE             = %.8f <DEGREE>\n' % uly)
    for northbc in tree.getiterator('northbc'):
        northbc.text = str(uly)
    #~ f.write('    WESTERNMOST_LONGITUDE        = %.8f <DEGREE>\n' % ulx)
    for westbc in tree.getiterator('westbc'):
        westbc.text = str(ulx)
    #~ f.write('    EASTERNMOST_LONGITUDE        = %.8f <DEGREE>\n' % lrx)
    for eastbc in tree.getiterator('eastbc'):
        eastbc.text = str(lrx)
    #~ f.write('    LINE_PROJECTION_OFFSET       = %.1f\n' % ( (ulx / kmres * 1000 ) - 0.5 ))
    #~ f.write('    SAMPLE_PROJECTION_OFFSET     = %.1f\n' % ( (uly / kmres * 1000 ) + 0.5 ))
    #~ f.write('END_OBJECT = IMAGE_MAP_PROJECTION\n')
    #~ f.write('\n')
    #~ f.write('OBJECT = IMAGE\n')
    #~ f.write('    NAME                       = \"%s\"\n' % (pszFilename))
    #~ f.write('    DESCRIPTION                = "Export data set from LMMP portal.\n')
    #~ f.write('                                 see filename for data type."\n')
    #~ #f.write('\n')
    #~ f.write('    LINES                      = %d\n' % hDataset.RasterYSize)
    for rowcount in tree.getiterator('rowcount'):
        rowcount.text = str(hDataset.RasterYSize)
    #~ f.write('    LINE_SAMPLES               = %d\n' % hDataset.RasterXSize)
    for colcount in tree.getiterator('colcount'):
        colcount.text = str(hDataset.RasterYSize)
    #~ f.write('    UNIT                       = METER\n')
    #~ f.write('    OFFSET                     = %.10g\n' % ( hBand.GetOffset() ))
    #~ f.write('    SCALING_FACTOR             = %.10g\n' % ( hBand.GetScale() ))
    #~ f.write('    SAMPLE_TYPE                = %s\n' % (sample_type) )
    #~ f.write('    SAMPLE_BITS                = %d\n' % (sample_bits) )
    #~ f.write('    SAMPLE_BIT_MASK            = %s\n' % (sample_mask) )
    #~ #f.write('\n')
    #~ f.write('    BANDS                      = %d\n' % hDataset.RasterCount)
    for vrtcount in tree.getiterator('vrtcount'):
        vrtcount.text = str(hDataset.RasterCount)
    #~ #f.write('\n')
    #~ f.write('    BAND_STORAGE_TYPE          = BAND_SEQUENTIAL\n')
    #~ if (sample_bits == 32) :
        #~ f.write('    CORE_NULL                  = 16#FF7FFFFB#\n')
        #~ f.write('    CORE_LOW_REPR_SATURATION   = 16#FF7FFFFC#\n')
        #~ f.write('    CORE_LOW_INSTR_SATURATION  = 16#FF7FFFFD#\n')
        #~ f.write('    CORE_HIGH_REPR_SATURATION  = 16#FF7FFFFF#\n')
        #~ f.write('    CORE_HIGH_INSTR_SATURATION = 16#FF7FFFFE#\n')
    #~ elif (sample_bits == 16) :
        #~ f.write('    CORE_NULL                  = -32768\n')
        #~ f.write('    CORE_LOW_REPR_SATURATION   = -32767\n')
        #~ f.write('    CORE_LOW_INSTR_SATURATION  = -32766\n')
        #~ f.write('    CORE_HIGH_REPR_SATURATION  = 32767\n')
        #~ f.write('    CORE_HIGH_INSTR_SATURATION = 32768\n')
    #~ else : #8bit
        #~ f.write('    CORE_NULL                  = 0\n')
        #~ f.write('    CORE_LOW_REPR_SATURATION   = 0\n')
        #~ f.write('    CORE_LOW_INSTR_SATURATION  = 0\n')
        #~ f.write('    CORE_HIGH_REPR_SATURATION  = 255\n')
        #~ f.write('    CORE_HIGH_INSTR_SATURATION = 255\n')
    #~ f.write('END_OBJECT = IMAGE\n')
    #~ f.write('END\n')
    #~ f.close()
    for metstdn in tree.getiterator('metstdn'):
        metstdn.text = "FGDC Content Standards for Digital Geospatial Metadata"
    for metstdv in tree.getiterator('metstdv'):
        metstdv.text = "FGDC-STD-001-1998"

#/* ==================================================================== */
#/*      writeout sparse XML for merging                                 */
#/* ==================================================================== */
    try:
        #tree.write(dst_xml, pretty_print=True, xml_declaration=True) #mp doesn't like declaration
        tree.write(dst_xml, pretty_print=True)
    except ImportError:
        print("Failed to write out XML document")
    
    return 0

#/************************************************************************/
#/*                        GDALInfoReportCorner()                        */
#/************************************************************************/

def GDALInfoReportCorner( hDataset, hTransform, corner_name, x, y ):

    line = "%-11s " % corner_name

#/* -------------------------------------------------------------------- */
#/*      Transform the point into georeferenced coordinates.             */
#/* -------------------------------------------------------------------- */
    adfGeoTransform = hDataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:
        dfGeoX = adfGeoTransform[0] + adfGeoTransform[1] * x \
            + adfGeoTransform[2] * y
        dfGeoY = adfGeoTransform[3] + adfGeoTransform[4] * x \
            + adfGeoTransform[5] * y

    else:
        line = line + ("(%7.1f,%7.1f)" % (x, y ))
        print(line)
        return False

#/* -------------------------------------------------------------------- */
#/*      Report the georeferenced coordinates.                           */
#/* -------------------------------------------------------------------- */
    if abs(dfGeoX) < 181 and abs(dfGeoY) < 91:
        line = line + ( "(%12.7f,%12.7f) " % (dfGeoX, dfGeoY ))

    else:
        line = line + ( "(%12.3f,%12.3f) " % (dfGeoX, dfGeoY ))

#/* -------------------------------------------------------------------- */
#/*      Transform to latlong and report.                                */
#/* -------------------------------------------------------------------- */
    if hTransform is not None:
        pnt = hTransform.TransformPoint(dfGeoX, dfGeoY, 0)
        if pnt is not None:
            line = line + ( "(%s," % gdal.DecToDMS( pnt[0], "Long", 2 ) )
            line = line + ( "%s)" % gdal.DecToDMS( pnt[1], "Lat", 2 ) )

    print(line)

    return True

#/************************************************************************/
#/*                        GDALGetLon()                              */
#/************************************************************************/
def GDALGetLon( hDataset, hTransform, x, y ):

#/* -------------------------------------------------------------------- */
#/*      Transform the point into georeferenced coordinates.             */
#/* -------------------------------------------------------------------- */
    adfGeoTransform = hDataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:
        dfGeoX = adfGeoTransform[0] + adfGeoTransform[1] * x \
            + adfGeoTransform[2] * y
        dfGeoY = adfGeoTransform[3] + adfGeoTransform[4] * x \
            + adfGeoTransform[5] * y
    else:
        return 0.0

#/* -------------------------------------------------------------------- */
#/*      Transform to latlong and report.                                */
#/* -------------------------------------------------------------------- */
    if hTransform is not None:
        pnt = hTransform.TransformPoint(dfGeoX, dfGeoY, 0)
        if pnt is not None:
          return pnt[0]
    return dfGeoX


#/************************************************************************/
#/*                        GDALGetLat()                              */
#/************************************************************************/

def GDALGetLat( hDataset, hTransform, x, y ):
#/* -------------------------------------------------------------------- */
#/*      Transform the point into georeferenced coordinates.             */
#/* -------------------------------------------------------------------- */
    adfGeoTransform = hDataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:
        dfGeoX = adfGeoTransform[0] + adfGeoTransform[1] * x \
            + adfGeoTransform[2] * y
        dfGeoY = adfGeoTransform[3] + adfGeoTransform[4] * x \
            + adfGeoTransform[5] * y
    else:
        return 0.0

#/* -------------------------------------------------------------------- */
#/*      Transform to latlong and report.                                */
#/* -------------------------------------------------------------------- */
    if hTransform is not None:
        pnt = hTransform.TransformPoint(dfGeoX, dfGeoY, 0)
        if pnt is not None:
          return pnt[1]
    return dfGeoY


#Parses attributes and texts and returns a list
#     Not currently used
def parse_XML(element):
    a = []
    for subelement in element:
        if subelement.text is None:
            a.append(subelement.attrib)
        else:
            a.append(subelement.text)
    return a

if __name__ == '__main__':
    version_num = int(gdal.VersionInfo('VERSION_NUM'))
    if version_num < 1800: # because of GetGeoTransform(can_return_null)
        print('ERROR: Python bindings of GDAL 1.8.0 or later required')
        sys.exit(1)

    sys.exit(main(sys.argv))
        
