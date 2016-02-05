#!/usr/bin/env python
#/******************************************************************************
# * $Id$
# *
# * Project: GDAL Utilities
# * Purpose: Create a ISIS3 compatible (raw w/ ISIS3 label) from a GDAL supported image.
# * Author:  Trent Hare, <thare@usgs.gov>
# * Date:    June 05, 2013
# * version: 0.1
# *
# * Port from gdalinfo.py whose author is Even Rouault
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
import datetime
import time
import os
import subprocess
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import gdal
    import osr

#/************************************************************************/
#/*                               Usage()                                */
#/************************************************************************/

def Usage(theApp):
    print( '\nUsage: Astropedia_gdal2ISIS3.py in.tif output.cub') # % theApp)
    print( '   optional: to print out image information also send -debug')
    print( '   optional: to just get a label *.lbl, send -noimage')
    print( '   optional: to attach the *.lbl to the ISIS image -attach - requires ISIS3')
    print( '   optional: to get lonsys=360, send -force360')
    print( '   optional: to override the center Longitude, send -centerLon 180')
    print( '   optional: to set scaler and offset send -base 17374000 and/or -multiplier 0.5')
    print( 'Usage: Astropedia_gdal2ISIS3.py -debug in.cub output.cub\n') # % theApp)
    print( 'Note: Currently this routine will only work for a limited set of images\n')
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
    bShowMetadata = False
    bShowRAT=False
    debug = False
    attach = False
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
    dst_cub = None
    dst_lbl = None
    dst_hst = None
    bands = 1
    centLat = 0
    centLon = 0
    centerLon = False
    TMscale = 1.0
    UpperLeftCornerX = 0
    UpperLeftCornerY = 0
    falseEast = 0
    falseNorth = 0
    bMakeImage = True
    force360 = False
    base = None
    multiplier = None

    #/* Must process GDAL_SKIP before GDALAllRegister(), but we can't call */
    #/* GDALGeneralCmdLineProcessor before it needs the drivers to be registered */
    #/* for the --format or --formats options */
    #for( i = 1; i < argc; i++ )
    #{
    #    if EQUAL(argv[i],"--config") and i + 2 < argc and EQUAL(argv[i + 1], "GDAL_SKIP"):
    #    {
    #        CPLSetConfigOption( argv[i+1], argv[i+2] );
    #
    #        i += 2;
    #    }
    #}
    #
    #GDALAllRegister();

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
            print("%s is running against GDAL %s" %
                   (argv[0], gdal.VersionInfo("RELEASE_NAME")))
            return 0
        elif EQUAL(argv[i], "-debug"):
            debug = True
        elif EQUAL(argv[i], "-attach"):
            attach = True
        elif EQUAL(argv[i], "-force360"):
            force360 = True
        elif EQUAL(argv[i], "-centerLon"):
		i = i + 1
		centerLon = float(argv[i])
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
        elif EQUAL(argv[i], "-noimage"):
            bMakeImage = False
        elif EQUAL(argv[i], "-base"):
            i = i + 1
            base = float(argv[i])
        elif EQUAL(argv[i], "-multiplier"):
            i = i + 1
            multiplier = float(argv[i])
        elif argv[i][0] == '-':
            return Usage(argv[0])
        elif pszFilename is None:
            pszFilename = argv[i]
        elif dst_cub is None:
            dst_cub = argv[i]
        else:
            return Usage(argv[0])

        i = i + 1

    if pszFilename is None:
        return Usage(argv[0])
    if dst_cub is None:
        return Usage(argv[0])

#/* -------------------------------------------------------------------- */
#/*      Open dataset.                                                   */
#/* -------------------------------------------------------------------- */
    hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly )
    if hDataset is None:
        print("gdalinfo failed - unable to open '%s'." % pszFilename )
        sys.exit(1)

    # Open the output file.
    if dst_cub is not None:
        dst_lbl = dst_cub.replace("CUB","LBL")
        dst_lbl = dst_lbl.replace("cub","lbl")
        dst_hst = dst_cub.replace("CUB","History.IsisCube")
        dst_hst = dst_hst.replace("cub","History.IsisCube")
        dst_hdr = dst_cub.replace("CUB","hdr")
        dst_hdr = dst_hdr.replace("cub","hdr")
        dst_aux = dst_cub.replace("CUB","cub.aux.xml")
        dst_aux = dst_aux.replace("cub","cub.aux.xml")
        if attach:
            attach_cub = dst_cub
            dst_cub = "XXX"+dst_cub
            dst_lbl = "XXX"+dst_lbl
            dst_hst = "XXX"+dst_hst
            dst_hdr = "XXX"+dst_hdr
            dst_aux = "XXX"+dst_aux
        if (EQUAL(dst_lbl,dst_cub)):
            print('Extension must be .CUB or .cub - unable to run using filename: %s' % pszFilename )
            sys.exit(1)
        else:
            f = open(dst_lbl,'wt')
            f_hst = open(dst_hst,'wt')

        
#    else:
#        f = sys.stdout
#        dst_cub = "out.cub"

#/* -------------------------------------------------------------------- */
#/*      Report general info.                                            */
#/* -------------------------------------------------------------------- */
    hDriver = hDataset.GetDriver();
    if debug:
        print( "Driver: %s/%s" % ( \
                hDriver.ShortName, \
                hDriver.LongName ))

    papszFileList = hDataset.GetFileList();
    if papszFileList is None or len(papszFileList) == 0:
        print( "Files: none associated" )
    else:
        if debug:
            print( "Files: %s" % papszFileList[0] )
            if bShowFileList:
                for i in range(1, len(papszFileList)):
                    print( "       %s" % papszFileList[i] )

    if debug:
        print( "Size is %d, %d" % (hDataset.RasterXSize, hDataset.RasterYSize))


#/* -------------------------------------------------------------------- */
#/*      Report projection.                                              */
#/* -------------------------------------------------------------------- */
    pszProjection = hDataset.GetProjectionRef()
    if pszProjection is not None:

        hSRS = osr.SpatialReference()
        if hSRS.ImportFromWkt(pszProjection ) == gdal.CE_None:
            pszPrettyWkt = hSRS.ExportToPrettyWkt(False)
            if debug:
                print( "Coordinate System is:\n%s" % pszPrettyWkt )
        else:
            if debug:
                print( "Coordinate System is `%s'" % pszProjection )


        hSRS = osr.SpatialReference()
        if hSRS.ImportFromWkt(pszProjection) == gdal.CE_None:
            pszPrettyWkt = hSRS.ExportToPrettyWkt(False)

            #print( "Coordinate System is:\n%s" % pszPrettyWkt )
            mapProjection = "None"
            #Extract projection information
            target = hSRS.GetAttrValue("DATUM",0)
            target = target.replace("D_","").replace("_2000","").replace("GCS_","")

            semiMajor = hSRS.GetSemiMajor() 
            semiMinor = hSRS.GetSemiMinor()
            if (pszProjection[0:6] == "GEOGCS"):
                mapProjection = "SimpleCylindrical"
                centLon = hSRS.GetProjParm('central_meridian')

            if (pszProjection[0:6] == "PROJCS"):
                mapProjection = hSRS.GetAttrValue("PROJECTION",0)

                if EQUAL(mapProjection,"Sinusoidal"):
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Equirectangular"):
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Transverse_Mercator"):
                    mapProjection = "TransverseMercator"
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')
                    TMscale = hSRS.GetProjParm('scale_factor')
                    #Need to research when TM actually applies false values
                    falseEast =  hSRS.GetProjParm('false_easting')
                    falseNorth =  hSRS.GetProjParm('false_northing')

                if EQUAL(mapProjection,"Orthographic"):
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Mercator_1SP"):
                    mapProjection = "Mercator"
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Mercator"):
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Polar_Stereographic"):
                    mapProjection = "PolarStereographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Stereographic_South_Pole"):
                    mapProjection = "PolarStereographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                
                if EQUAL(mapProjection,"Stereographic_North_Pole"):
                    mapProjection = "PolarStereographic"
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
            if debug:
                print( "Coordinate System is:\n%s" % pszPrettyWkt )
        else:
            print( "Warning - Currently we can't parse this type of projection" )
            print( "Coordinate System is `%s'" % pszProjection )
            target = "n/a"
            #sys.exit(1)
    else:
        print( "Warning - No Coordinate System defined:\n" )
        target = "n/a"
        #sys.exit(1)
        
#/* -------------------------------------------------------------------- */
#/*      Report Geotransform.                                            */
#/* -------------------------------------------------------------------- */
    adfGeoTransform = hDataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:
        UpperLeftCornerX = adfGeoTransform[0] - falseEast
        UpperLeftCornerY = adfGeoTransform[3] - falseNorth

        if adfGeoTransform[2] == 0.0 and adfGeoTransform[4] == 0.0:
            if debug:
                print( "Origin = (%.15f,%.15f)" % ( \
                        adfGeoTransform[0], adfGeoTransform[3] ))

                print( "Pixel Size = (%.15f,%.15f)" % ( \
                        adfGeoTransform[1], adfGeoTransform[5] ))

        else:
            if debug:
                print( "GeoTransform =\n" \
                        "  %.16g, %.16g, %.16g\n" \
                        "  %.16g, %.16g, %.16g" % ( \
                        adfGeoTransform[0], \
                        adfGeoTransform[1], \
                        adfGeoTransform[2], \
                        adfGeoTransform[3], \
                        adfGeoTransform[4], \
                        adfGeoTransform[5] ))

        #Using a very simple method to calculate cellsize. 
        #Warning: might not always be good.
        if (pszProjection[0:6] == "GEOGCS"):
            #convert degrees/pixel to m/pixel 
             mapres = 1 / adfGeoTransform[1]
             mres = adfGeoTransform[1] * (semiMajor * math.pi / 180.0)
        else:
            #convert m/pixel to pixel/degree
             mapres = 1 / (adfGeoTransform[1] / (semiMajor * math.pi / 180.0))
             mres = adfGeoTransform[1] 

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
                    print( "GCP Projection = \n%s" % pszPrettyWkt )

            else:
                if debug:
                    print( "GCP Projection = %s" % \
                            pszProjection )

        gcps = hDataset.GetGCPs()
        i = 0
        for gcp in gcps:
            if debug:
                print( "GCP[%3d]: Id=%s, Info=%s\n" \
                        "          (%.15g,%.15g) -> (%.15g,%.15g,%.15g)" % ( \
                        i, gcp.Id, gcp.Info, \
                        gcp.GCPPixel, gcp.GCPLine, \
                        gcp.GCPX, gcp.GCPY, gcp.GCPZ ))
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
                print( "  %s" % metadata )

        if bShowMetadata:
            for extra_domain in papszExtraMDDomains:
                papszMetadata = hDataset.GetMetadata_List(extra_domain)
                if papszMetadata is not None and len(papszMetadata) > 0 :
                    print( "Metadata (%s):" % extra_domain)
                    for metadata in papszMetadata:
                      print( "  %s" % metadata )

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
                print( "  %s" % metadata )

#/* -------------------------------------------------------------------- */
#/*      Report subdatasets.                                             */
#/* -------------------------------------------------------------------- */
        papszMetadata = hDataset.GetMetadata_List("SUBDATASETS")
        if papszMetadata is not None and len(papszMetadata) > 0 :
            print( "Subdatasets:" )
            for metadata in papszMetadata:
                print( "  %s" % metadata )

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
                print( "  %s" % metadata )

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
                print( "  %s" % metadata )

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
   
    if (centerLon):
       centLon = centerLon
 
    #Calculate Simple Cylindrical X,Y in meters from bounds if not projected.
    #Needs testing.                     
    if (pszProjection[0:6] == "GEOGCS"):
        #note that: mres = adfGeoTransform[1] * (semiMajor * math.pi / 180.0)
        UpperLeftCornerX = semiMajor * (ulx - centLon) * math.pi / 180.0
        UpperLeftCornerY = semiMajor * uly * math.pi / 180.0
        

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
                print( "Band %d Block=%dx%d Type=%s, ColorInterp=%s" % ( iBand+1, \
                                nBlockXSize, nBlockYSize, \
                                gdal.GetDataTypeName(hBand.DataType), \
                                gdal.GetColorInterpretationName( \
                                        hBand.GetRasterColorInterpretation()) ))

                if hBand.GetDescription() is not None \
                        and len(hBand.GetDescription()) > 0 :
                        print( "  Description = %s" % hBand.GetDescription() )

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
                        print( "  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                                        stats[0], stats[1], stats[2], stats[3] ))

                if bReportHistograms:

                        hist = hBand.GetDefaultHistogram(force = True, callback = gdal.TermProgress)
                        if hist is not None:
                                dfMin = hist[0]
                                dfMax = hist[1]
                                nBucketCount = hist[2]
                                panHistogram = hist[3]

                                print( "  %d buckets from %g to %g:" % ( \
                                                nBucketCount, dfMin, dfMax ))
                                line = '  '
                                for bucket in panHistogram:
                                        line = line + ("%d " % bucket)

                                print(line)

                if bComputeChecksum:
                        print( "  Checksum=%d" % hBand.Checksum())

                dfNoData = hBand.GetNoDataValue()
                if dfNoData is not None:
                        if dfNoData != dfNoData:
                                print( "  NoData Value=nan" )
                        else:
                                print( "  NoData Value=%.18g" % dfNoData )

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
                        print( "  Unit Type: %s" % hBand.GetUnitType())

                papszCategories = hBand.GetRasterCategoryNames()
                if papszCategories is not None:

                        print( "  Categories:" );
                        i = 0
                        for category in papszCategories:
                                print( "    %3d: %s" % (i, category) )
                                i = i + 1

                if hBand.GetScale() != 1.0 or hBand.GetOffset() != 0.0:
                        print( "  Offset: %.15g,   Scale:%.15g" % \
                                                ( hBand.GetOffset(), hBand.GetScale()))

                if bShowMetadata:
                        papszMetadata = hBand.GetMetadata_List()
                else:
                        papszMetadata = None
                if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
                        print( "  Metadata:" )
                        for metadata in papszMetadata:
                                print( "    %s" % metadata )


                if bShowMetadata:
                        papszMetadata = hBand.GetMetadata_List("IMAGE_STRUCTURE")
                else:
                        papszMetadata = None
                if bShowMetadata and papszMetadata is not None and len(papszMetadata) > 0 :
                        print( "  Image Structure Metadata:" )
                        for metadata in papszMetadata:
                                print( "    %s" % metadata )


                hTable = hBand.GetRasterColorTable()
                if hBand.GetRasterColorInterpretation() == gdal.GCI_PaletteIndex  \
                        and hTable is not None:

                        print( "  Color Table (%s with %d entries)" % (\
                                        gdal.GetPaletteInterpretationName( \
                                                hTable.GetPaletteInterpretation(  )), \
                                        hTable.GetCount() ))

                        if bShowColorTable:

                                for i in range(hTable.GetCount()):
                                        sEntry = hTable.GetColorEntry(i)
                                        print( "  %3d: %d,%d,%d,%d" % ( \
                                                        i, \
                                                        sEntry[0],\
                                                        sEntry[1],\
                                                        sEntry[2],\
                                                        sEntry[3] ))

                if bShowRAT:
                        hRAT = hBand.GetDefaultRAT()

            #GDALRATDumpReadable( hRAT, None );

#/***************************************************************************/
#/*                           WriteISISlabel()                              */
#/***************************************************************************/
#def WriteISISLabel(outFile, DataSetID, pszFilename, sampleBits, lines, samples):
#Currently just procedural programming. Gets the job done...
#
    instrList = pszFilename.split("_")
    hBand = hDataset.GetRasterBand( 1 )
    #get the datatype
    print gdal.GetDataTypeName(hBand.DataType)
    if EQUAL(gdal.GetDataTypeName(hBand.DataType), "Float32"):
        sample_bits = 32
        sample_type = "Real"
        sample_mask = "2#11111111111111111111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "Float64"):
        sample_bits = 32
        sample_type = "Real"
        sample_mask = "2#11111111111111111111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "INT16"):
        sample_bits = 16
        sample_type = "SignedWord"
        sample_mask = "2#1111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "UINT16"):
        sample_bits = 16
        sample_type = "UsignedWord"
        sample_mask = "2#1111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "Byte"):
        sample_bits = 8
        sample_type = "UnsignedByte"
        sample_mask = "2#11111111#"
    else:
        print( "  %s: Not supported pixel type. Please convert to 8, 16 Int, or 32 Float" % gdal.GetDataTypeName(hBand.DataType))
        sys.exit(1)

    f.write('Object = IsisCube\n')
    f.write('  Object = Core\n')
    f.write('    StartByte = 1\n')
    #f.write('/* The source image data definition. */\n')
    f.write('    ^Core     = %s\n' % (dst_cub))
    f.write('    Format    = BandSequential\n')
    f.write('\n')
    f.write('    Group = Dimensions\n')
    f.write('      Samples = %d\n' % (hDataset.RasterXSize))
    f.write('      Lines   = %d\n' % hDataset.RasterYSize)
    f.write('      Bands   = %d\n' % hDataset.RasterCount)
    f.write('    End_Group\n')
    f.write('\n')
    f.write('    Group = Pixels\n')
    f.write('      Type       = %s\n' % (sample_type))
    f.write('      ByteOrder  = Lsb\n')
    if base is None: 
        f.write('      Base       = %.10g\n' % ( hBand.GetOffset() ))
        if EQUAL(sample_type, "REAL"):
           if (hBand.GetOffset() <> 0):
              print("Warning: a none 0 'base' was set but input is 32bit Float. ISIS will not use this value when type is REAL. Please use 'fx' to apply this base value: %.10g" % ( hBand.GetOffset() ))
    else:
        f.write('      Base       = %.10g\n' % base )
        if EQUAL(sample_type, "REAL"):
            print("Warning: '-base' was set but input is 32bit Float. ISIS will not use this value when type is REAL. Please use 'fx' to apply this base value.")
    if multiplier is None: 
        f.write('      Multiplier = %.10g\n' % ( hBand.GetScale() ))
        if EQUAL(sample_type, "REAL"):
           if (hBand.GetScale() <> 1):
              print("Warning: a none 1 'multiplier' was set but input is 32bit Float. ISIS will not use this value when type is REAL. Please use 'fx' to apply this multiplier value: %.10g" % ( hBand.GetScale() ))
    else:
        f.write('      Multiplier = %.10g\n' % multiplier )
        if EQUAL(sample_type, "REAL"):
            print("Warning: '-multiplier' was set but input is 32bit Float. ISIS will not use this value when type is REAL. Please use 'fx' to apply this multiplier value.")
    f.write('    End_Group\n')
    f.write('  End_Object\n')
    f.write('\n')
    f.write('  Group = Archive\n')
    f.write('    DataSetId               = %s\n' %  pszFilename.split(".")[0])
    f.write('    ProducerInstitutionName = \"Astrogeology Science Center\"\n')
    f.write('    ProducerId              = Astrogeology\n')
    f.write('    ProducerFullName        = USGS\n')
    if "_v" in pszFilename:
        f.write('    ProductId               = %s\n' % instrList[-1].split(".")[0].upper())
    else:
        f.write('    ProductId               = n/a\n')
    f.write('    ProductVersionId        = n/a\n')
    f.write('    InstrumentHostName      = n/a\n')
    f.write('    InstrumentName          = n/a\n')
    f.write('    InstrumentId            = n/a\n')
    f.write('    TargetName              = %s\n' % target)
    f.write('    MissionPhaseName        = n/a\n')
    f.write('  End_Group\n')
    f.write('\n')
    if target <> "n/a":
        f.write('  Group = Mapping\n')
        f.write('    ProjectionName          = %s\n' % mapProjection)
        if ((centLon < 0) and force360):
          centLon = centLon + 360  
        f.write('    CenterLongitude         = %.5f\n' % centLon)
        f.write('    CenterLatitude          = %.5f\n' % centLat)
        if EQUAL(mapProjection,"TransverseMercator"):
          f.write('    ScaleFactor             = %6.5f\n' % TMscale)
        f.write('    TargetName              = %s\n' % target)
        f.write('    EquatorialRadius        = %.1f <meters>\n' % semiMajor)
        f.write('    PolarRadius             = %.1f <meters>\n' % semiMinor)
        if EQUAL(mapProjection,"TransverseMercator"):
          f.write('    LatitudeType            = Planetographic\n')
        else:
          f.write('    LatitudeType            = Planetocentric\n')
        f.write('    LongitudeDirection      = PositiveEast\n')
        if (force360 or (lrx > 180)):
          f.write('    LongitudeDomain         = 360\n')
        else:
          f.write('    LongitudeDomain         = 180\n')
        f.write('    PixelResolution         = %.8f <meters/pixel>\n' % mres )
        f.write('    Scale                   = %.4f <pixel/degree>\n' % mapres )
        if lry < uly:
          f.write('    MinimumLatitude         = %.8f\n' % lry)
          f.write('    MaximumLatitude         = %.8f\n' % uly)
        else:
          f.write('    MinimumLatitude         = %.8f\n' % uly)
          f.write('    MaximumLatitude         = %.8f\n' % lry)

        #push into 360 domain (for Astropedia)
        if (force360):
          if (ulx < 0):
             ulx = ulx + 360
          if (lrx < 0):
             lrx = lrx + 360
        if lrx < ulx:
            f.write('    MinimumLongitude        = %.8f\n' % lrx)
            f.write('    MaximumLongitude        = %.8f\n' % ulx)
        else:
          f.write('    MinimumLongitude        = %.8f\n' % ulx)
          f.write('    MaximumLongitude        = %.8f\n' % lrx)
        f.write('    UpperLeftCornerX        = %.6f <meters>\n' % ( UpperLeftCornerX ))
        f.write('    UpperLeftCornerY        = %.6f <meters>\n' % ( UpperLeftCornerY ))
        f.write('  End_Group\n')
    f.write('End_Object\n')
    f.write('\n')
    f.write('Object = Label\n')
    #NOT correct
    f.write('  Bytes = 256\n')
    f.write('End_Object\n')
    f.write('\n')
    f.write('Object = History\n')
    f.write('  Name           = IsisCube\n')
    f.write('  StartByte      = 1\n')
    #NOT correct
    f.write('  Bytes          = 256\n')
    f.write('  ^History       = %s\n' % dst_hst)
    f.write('End_Object\n')
    f.write('End\n')
    f.close()
    
    f_hst.write('Object = Astropedia_gdal2isis.py\n')
    f_hst.write('  Version           = 0.1\n')
    f_hst.write('  ProgramVersion    = 2013-06-05\n')
    f_hst.write('  ExecutionDateTime = %s\n' % str(datetime.datetime.now().isoformat()))
    f_hst.write('  Description        = \"Convert GDAL supported image to an ISIS detached label and raw image\"\n')
    f_hst.write('End_Object\n')
    f_hst.close()

    #########################
    #Export out raw image
    #########################
    #Setup the output dataset
    print (' - ISIS3 label created:   %s' % dst_lbl)
    print (' - ISIS3 history created: %s' % dst_hst)
    if bMakeImage:
      print ('Please wait, writing out raw image: %s' % dst_cub)
      driver = gdal.GetDriverByName('ENVI')
      output = driver.CreateCopy(dst_cub, hDataset, 1) 
    if attach:
      #print 'sleeping 5 seconds'
      #time.sleep(5)
      cmd = "/usgs/cdev/contrib/bin/run_cubeatt.sh %s %s" % (dst_lbl, attach_cub)
      #cmd = "cubeatt from=%s to=%s\n" % (dst_lbl, attach_cub)
      print cmd
      #subprocess.call(cmd, shell=True)
      os.system(cmd)
      os.remove(dst_cub)
      os.remove(dst_lbl)
      os.remove(dst_hst)
      os.remove(dst_hdr)
      os.remove(dst_aux)
    print ('Complete')
    
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

if __name__ == '__main__':
    version_num = int(gdal.VersionInfo('VERSION_NUM'))
    if version_num < 1800: # because of GetGeoTransform(can_return_null)
        print('ERROR: Python bindings of GDAL 1.8.0 or later required')
        sys.exit(1)

    sys.exit(main(sys.argv))
        
