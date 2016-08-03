#!/usr/bin/env python
#/******************************************************************************
# * $Id$
# *
# * Project:  GDAL Utilities
# * Purpose:  Create a PDS compatible (raw w PDS label) from a GDAL supported image.
# *             Currently only LMMP projections supported (geographic, 
# *             equirectangular, polar_stereographic)
# * Author:   Trent Hare, <thare at usgs dot gov>
# * Date:     July 20, 2011
# * version:  0.1
# *
# * Port from gdalinfo.py whose author is Even Rouault
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

#/************************************************************************/
#/*                               Usage()                                */
#/************************************************************************/

def Usage(theApp):
    print( '\nUsage: LMMP_gdal2PDS in.tif output.img') # % theApp)
    print( '   optional: to print out image information also send -debug')
    print( 'Usage: LMMP_gdal2PDS -debug in.tif output.img\n') # % theApp)
    print( 'Note: Currently this routine only supports LMMP products in')
    print('      (geographic, equirectangular, polar_stereographic)\n')
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
    dst_img = None
    dst_lbl = None
    bands = 1

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
        elif dst_img is None:
            dst_img = argv[i]
        else:
            return Usage(argv[0])

        i = i + 1

    if pszFilename is None:
        return Usage(argv[0])
    if dst_img is None:
        return Usage(argv[0])

#/* -------------------------------------------------------------------- */
#/*      Open dataset.                                                   */
#/* -------------------------------------------------------------------- */
    hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly )
    if hDataset is None:
        print("gdalinfo failed - unable to open '%s'." % pszFilename )
        sys.exit(1)

    # Open the output file.
    if dst_img is not None:
        dst_lbl = dst_img.replace("IMG","LBL")
        dst_lbl = dst_lbl.replace("img","lbl")
        if (EQUAL(dst_lbl,dst_img)):
            print('Extension must be .IMG or .img - unable to run using filename: %s' % pszFilename )
            sys.exit(1)
        else:
            f = open(dst_lbl,'wt')
#    else:
#        f = sys.stdout
#        dst_img = "out.img"

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

            #print( "Coordinate System is:\n%s" % pszPrettyWkt )
            mapProjection = "None"
            #Extract projection information
            target = hSRS.GetAttrValue("DATUM",0).replace("D_","").replace("_2000","")
            semiMajor = hSRS.GetSemiMajor() / 1000.0
            semiMinor = hSRS.GetSemiMinor() / 1000.0
            if (pszProjection[0:6] == "GEOGCS"):
                mapProjection = "SIMPLE_CYLINDRICAL"
                centLat = 0
                centLon = 0
            if (pszProjection[0:6] == "PROJCS"):
                mapProjection = hSRS.GetAttrValue("PROJECTION",0)

                if EQUAL(mapProjection,"Equirectangular"):
                    centLat = hSRS.GetProjParm('standard_parallel_1')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Polar_Stereographic"):
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')

                if EQUAL(mapProjection,"Stereographic_South_Pole"):
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
                
                if EQUAL(mapProjection,"Stereographic_North_Pole"):
                    centLat = hSRS.GetProjParm('latitude_of_origin')
                    centLon = hSRS.GetProjParm('central_meridian')
            if debug:
                print( "Coordinate System is:\n%s" % pszPrettyWkt )
        else:
            print( "Warning - Can't parse this type of projection\n" )
            print( "Coordinate System is `%s'" % pszProjection )
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

        if (pszProjection[0:6] == "GEOGCS"):
            #convert degrees/pixel to km/pixel 
             mapres = 1 / adfGeoTransform[1]
             kmres = adfGeoTransform[1] * (semiMajor * math.pi / 180.0)
        else:
            #convert m/pixel to pixel/degree
             mapres = 1 / (adfGeoTransform[1] / (semiMajor * 1000.0 * math.pi / 180.0))
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

#/************************************************************************/
#/*                           WritePDSlabel()                            */
#/************************************************************************/
#def WritePDSlabel(outFile, DataSetID, pszFilename, sampleBits, lines, samples):
    instrList = pszFilename.split("_")
    hBand = hDataset.GetRasterBand( 1 )
    #get the datatype
    if EQUAL(gdal.GetDataTypeName(hBand.DataType), "Float32"):
        sample_bits = 32
        sample_type = "PC_REAL"
        sample_mask = "2#11111111111111111111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "INT16"):
        sample_bits = 16
        sample_type = "LSB_INTEGER"
        sample_mask = "2#1111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "UINT16"):
        sample_bits = 16
        sample_type = "UNSIGNED_INTEGER"
        sample_mask = "2#1111111111111111#"
    elif EQUAL(gdal.GetDataTypeName(hBand.DataType), "Byte"):
        sample_bits = 8
        sample_type = "UNSIGNED_INTEGER"
        sample_mask = "2#11111111#"
    else:
        print( "  %s: Not supported pixel type" % gdal.GetDataTypeName(hBand.DataType))
        sys.exit(1)

    f.write('PDS_VERSION_ID            = PDS3\n')
    f.write('\n')
    f.write('/* The source image data definition. */\n')
    f.write('FILE_NAME      = \"%s\"\n' % (dst_img))
    f.write('RECORD_TYPE   = FIXED_LENGTH\n')
    f.write('RECORD_BYTES  = %d\n' % (hDataset.RasterYSize))
    f.write('FILE_RECORDS  = %d\n' % ((hDataset.RasterXSize * sample_bits / 8)) )
    #f.write('LABEL_RECORDS = 1\n')
    f.write('^IMAGE        = \"%s\"\n' % (dst_img))
    f.write('\n')
    f.write('/* Identification Information  */\n')
    f.write('DATA_SET_ID               = "%s"\n' % pszFilename.split(".")[0])
    f.write('DATA_SET_NAME             = "%s"\n' % pszFilename.split(".")[0])
    f.write('PRODUCER_INSTITUTION_NAME = "Lunar Mapping and Modeling Project"\n')
    f.write('PRODUCER_ID               = "LMMP_TEAM"\n')
    f.write('PRODUCER_FULL_NAME        = "LMMP TEAM"\n')
    f.write('PRODUCT_ID                = "%s"\n' % pszFilename.split(".")[0])
    if "_v" in pszFilename:
        f.write('PRODUCT_VERSION_ID        = "%s.0"\n' % instrList[-1].split(".")[0].upper())
    else:
        f.write('PRODUCT_VERSION_ID        = "%s"\n' % "V1.0")
    f.write('PRODUCT_TYPE              = "RDR"\n')
    f.write('INSTRUMENT_HOST_NAME      = "%s"\n' % instrList[0])
    f.write('INSTRUMENT_HOST_ID        = "%s"\n' % instrList[0])
    f.write('INSTRUMENT_NAME           = "%s"\n' % instrList[1])
    f.write('INSTRUMENT_ID             = "%s"\n' % instrList[1])
    f.write('TARGET_NAME               = MOON\n')
    f.write('MISSION_PHASE_NAME        = "POST MISSION"\n')
    f.write('RATIONALE_DESC            = "Created at the request of NASA\'s Exploration\n')
    f.write('                            Systems Mission Directorate to support future\n')
    f.write('                            human exploration"\n')
    f.write('SOFTWARE_NAME             = "ISIS 3.2.1 | SOCET SET v5.5 (r) BAE Systems\n')
    f.write('                            | GDAL 1.8"\n')
    f.write('\n')
    f.write('/* Time Parameters */\n')
    f.write('START_TIME                   = "N/A"\n')
    f.write('STOP_TIME                    = "N/A"\n')
    f.write('SPACECRAFT_CLOCK_START_COUNT = "N/A"\n')
    f.write('SPACECRAFT_CLOCK_STOP_COUNT  = "N/A"\n')
    f.write('PRODUCT_CREATION_TIME        = %s\n' % strftime("%Y-%m-%dT%H:%M:%S"))   #2011-03-11T22:13:40
    f.write('\n')
    f.write('OBJECT = IMAGE_MAP_PROJECTION\n')
    f.write('    ^DATA_SET_MAP_PROJECTION     = "DSMAP.CAT"\n')
    f.write('    MAP_PROJECTION_TYPE          = \"%s\"\n' % mapProjection)
    f.write('    PROJECTION_LATITUDE_TYPE     = PLANETOCENTRIC\n')
    f.write('    A_AXIS_RADIUS                = %.1f <KM>\n' % semiMajor)
    f.write('    B_AXIS_RADIUS                = %.1f <KM>\n' % semiMajor)
    f.write('    C_AXIS_RADIUS                = %.1f <KM>\n' % semiMinor)
    f.write('    COORDINATE_SYSTEM_NAME       = PLANETOCENTRIC\n')
    f.write('    POSITIVE_LONGITUDE_DIRECTION = EAST\n')
    f.write('    KEYWORD_LATITUDE_TYPE        = PLANETOCENTRIC\n')
    f.write('    /* NOTE:  CENTER_LATITUDE and CENTER_LONGITUDE describe the location   */\n')
    f.write('    /* of the center of projection, which is not necessarily equal to the  */\n')
    f.write('    /* location of the center point of the image.                          */\n')
    f.write('    CENTER_LATITUDE              = %5.2f <DEG>\n' % centLat)
    f.write('    CENTER_LONGITUDE             = %5.2f <DEG>\n' % centLon)
    f.write('    LINE_FIRST_PIXEL             = 1\n')
    f.write('    LINE_LAST_PIXEL              = %d\n' % hDataset.RasterYSize)
    f.write('    SAMPLE_FIRST_PIXEL           = 1\n')
    f.write('    SAMPLE_LAST_PIXEL            = %d\n' % hDataset.RasterXSize)
    f.write('    MAP_PROJECTION_ROTATION      = 0.0 <DEG>\n')
    f.write('    MAP_RESOLUTION               = %.4f <PIX/DEG>\n' % mapres )
    f.write('    MAP_SCALE                    = %.8f <KM/PIXEL>\n' % kmres )
    f.write('    MINIMUM_LATITUDE             = %.8f <DEGREE>\n' % lry)
    f.write('    MAXIMUM_LATITUDE             = %.8f <DEGREE>\n' % uly)
    f.write('    WESTERNMOST_LONGITUDE        = %.8f <DEGREE>\n' % ulx)
    f.write('    EASTERNMOST_LONGITUDE        = %.8f <DEGREE>\n' % lrx)
    f.write('    LINE_PROJECTION_OFFSET       = %.1f\n' % ( (ulx / kmres * 1000 ) - 0.5 ))
    f.write('    SAMPLE_PROJECTION_OFFSET     = %.1f\n' % ( (uly / kmres * 1000 ) + 0.5 ))
    f.write('END_OBJECT = IMAGE_MAP_PROJECTION\n')
    f.write('\n')
    f.write('OBJECT = IMAGE\n')
    f.write('    NAME                       = \"%s\"\n' % (pszFilename))
    f.write('    DESCRIPTION                = "Export data set from LMMP portal.\n')
    f.write('                                 see filename for data type."\n')
    #f.write('\n')
    f.write('    LINES                      = %d\n' % hDataset.RasterYSize)
    f.write('    LINE_SAMPLES               = %d\n' % hDataset.RasterXSize)
    f.write('    UNIT                       = METER\n')
    f.write('    OFFSET                     = %.10g\n' % ( hBand.GetOffset() ))
    f.write('    SCALING_FACTOR             = %.10g\n' % ( hBand.GetScale() ))
    f.write('    SAMPLE_TYPE                = %s\n' % (sample_type) )
    f.write('    SAMPLE_BITS                = %d\n' % (sample_bits) )
    f.write('    SAMPLE_BIT_MASK            = %s\n' % (sample_mask) )
    #f.write('\n')
    f.write('    BANDS                      = %d\n' % hDataset.RasterCount)
    #f.write('\n')
    f.write('    BAND_STORAGE_TYPE          = BAND_SEQUENTIAL\n')
    if (sample_bits == 32) :
        f.write('    CORE_NULL                  = 16#FF7FFFFB#\n')
        f.write('    CORE_LOW_REPR_SATURATION   = 16#FF7FFFFC#\n')
        f.write('    CORE_LOW_INSTR_SATURATION  = 16#FF7FFFFD#\n')
        f.write('    CORE_HIGH_REPR_SATURATION  = 16#FF7FFFFF#\n')
        f.write('    CORE_HIGH_INSTR_SATURATION = 16#FF7FFFFE#\n')
    elif (sample_bits == 16) :
        f.write('    CORE_NULL                  = -32768\n')
        f.write('    CORE_LOW_REPR_SATURATION   = -32767\n')
        f.write('    CORE_LOW_INSTR_SATURATION  = -32766\n')
        f.write('    CORE_HIGH_REPR_SATURATION  = 32767\n')
        f.write('    CORE_HIGH_INSTR_SATURATION = 32768\n')
    else : #8bit
        f.write('    CORE_NULL                  = 0\n')
        f.write('    CORE_LOW_REPR_SATURATION   = 0\n')
        f.write('    CORE_LOW_INSTR_SATURATION  = 0\n')
        f.write('    CORE_HIGH_REPR_SATURATION  = 255\n')
        f.write('    CORE_HIGH_INSTR_SATURATION = 255\n')
    f.write('END_OBJECT = IMAGE\n')
    f.write('END\n')
    f.close()
    
    #########################
    #Export out raw image
    #########################
    #Setup the output dataset
    print ('Please wait, writing out raw image: %s' % dst_img)
    driver = gdal.GetDriverByName('ENVI')
    output = driver.CreateCopy(dst_img, hDataset, 1) 
    print ('Complete. PDS label also created: %s' % dst_lbl)
    
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
        
