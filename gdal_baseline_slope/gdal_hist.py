#!/usr/bin/env python
#/******************************************************************************
# * $Id$
# *
# * Project:  GDAL Histogram
# * Purpose:  Export an image histogram in xls format
# * Author:   Trent Hare, thare@usgs.gov
# *   based on code by Even Rouault, <even dot rouault at mines dash paris dot org>
# *
# * Port from gdalinfo.c whose author is Frank Warmerdam
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
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import gdal
    import osr

#/************************************************************************/
#/*                               Usage()                                */
#/************************************************************************/

def Usage():
    print( "Usage: gdalhist [-mm] [-stats] [-hist] [-unscale] datasetname")
    print( "  Note: at least one flag must be sent")
    return 1


def EQUAL(a, b):
    return a.lower() == b.lower()

#/************************************************************************/
#/*                                main()                                */
#/************************************************************************/

def main( argv = None ):

    bReportHistograms = False
    bApproxStats = False
    scale = 1.0
    offset = 0.0

    bComputeMinMax = False
    bSample = False
    bShowGCPs = True
    bShowMetadata = True
    bShowRAT=True
    bStats = False
    bScale = False
    bShowColorTable = True
    pszFilename = None
    papszExtraMDDomains = [ ]
    pszProjection = None
    hTransform = None

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
        elif EQUAL(argv[i], "-mm"):
            bComputeMinMax = True
        elif EQUAL(argv[i], "-unscale"):
            bScale = True
        elif EQUAL(argv[i], "-stats"):
            bStats = True
        elif EQUAL(argv[i], "-hist"):
             bReportHistograms = True
        elif argv[i][0] == '-':
            return Usage()
        elif pszFilename is None:
            pszFilename = argv[i]
        else:
            return Usage()

        i = i + 1

    if pszFilename is None:
        return Usage()
    if not (bComputeMinMax or bScale or bStats or bReportHistograms):
        return Usage()

#/* -------------------------------------------------------------------- */
#/*      Open dataset.                                                   */
#/* -------------------------------------------------------------------- */
    hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly )

    if hDataset is None:
        print("gdalinfo failed - unable to open '%s'." % pszFilename )
        return 1
    
#/* ==================================================================== */
#/*      Loop over bands.                                                */
#/* ==================================================================== */
    for iBand in range(hDataset.RasterCount):
        hBand = hDataset.GetRasterBand(iBand+1 )
        (nBlockXSize, nBlockYSize) = hBand.GetBlockSize()

        if bScale:
             offset = hBand.GetOffset() 
             if offset is None:
                  offset = 0.0
             scale = hBand.GetScale()
             if scale is None:
                  scale = 1.0

        if (hDataset.RasterCount > 1):
           print( "Band %d Block=%dx%d Type=%s, ColorInterp=%s" % ( iBand+1, \
                nBlockXSize, nBlockYSize, \
                gdal.GetDataTypeName(hBand.DataType), \
                gdal.GetColorInterpretationName( \
                hBand.GetRasterColorInterpretation()) ))

        dfMin = hBand.GetMinimum()
        dfMax = hBand.GetMaximum()
        if dfMin is not None or dfMax is not None or bComputeMinMax:

            line =  ""
            if dfMin is not None:
                dfMin = (dfMin * scale) + offset
                line = line + ("Min=%.3f " % (dfMin))
            if dfMax is not None:
                dfMax = (dfMax * scale) + offset
                line = line + ("Max=%.3f " % (dfMax))

            if bComputeMinMax:
                gdal.ErrorReset()
                adfCMinMax = hBand.ComputeRasterMinMax(True)
                if gdal.GetLastErrorType() == gdal.CE_None:
                  line = line + ( "  Computed Min/Max=%.3f,%.3f" % ( \
                          ((adfCMinMax[0] * scale) + offset), \
                          ((adfCMinMax[1] * scale) + offset) ))
                  print( line )

            #if bStats:
            #   print( line )

        stats = hBand.GetStatistics( bApproxStats, bStats)
        #inType = gdal.GetDataTypeName(hBand.DataType)

        # Dirty hack to recognize if stats are valid. If invalid, the returned
        # stddev is negative
        if stats[3] >= 0.0:
            if bStats:
                  mean =  (stats[2] * scale) + offset;
                  stdev = (stats[3] * scale) + offset;
                  rms = math.sqrt((mean * mean) + ( stdev * stdev))
                  print( "Min=%.2f, Max=%.2f, Mean=%.2f, StdDev=%.2f, RMS=%.2f" \
                    % ((stats[0] * scale) + offset, (stats[1] * scale) + offset,\
                       mean, stdev, rms ))

        if bReportHistograms:
            print ("level\tvalue\tcount\tcumlative")

            #Histogram call not returning exact min and max. 
            #...Workaround run gdalinfo -stats and then use min/max from above

            hist = hBand.GetDefaultHistogram(force = True)
            #hist = hBand.GetDefaultHistogram(force = True, callback = gdal.TermProgress)
            cnt = 0
            sum = 0
            sumTotal = 0
            if hist is not None:
                #use dfMin and dfMax from previous calls when possible
                if dfMin is None:
                   dfMin = (hist[0] * scale) + offset
                if dfMax is None:
                   dfMax = (hist[1] * scale) + offset
                nBucketCount = hist[2]
                panHistogram = hist[3]

                #print( "  %d buckets from %g to %g:" % ( \
                #        nBucketCount, dfMin, dfMax ))
                #print ( "scale: %g, offset: %g" % (scale, offset))
                increment = round(((dfMax - dfMin) / nBucketCount),2)
                value = dfMin
                #get total to normalize (below)
                for bucket in panHistogram:
                    sumTotal = sumTotal + bucket
                for bucket in panHistogram:
                    sum = sum + bucket
                    #normalize cumlative
                    nsum = sum  / float(sumTotal)
                    line = "%d\t%0.2f\t%d\t%0.6f" % (cnt, value, bucket, nsum)
                    print(line)
                    cnt = cnt + 1
                    value = value + increment

    return True

if __name__ == '__main__':
    version_num = int(gdal.VersionInfo('VERSION_NUM'))
    if version_num < 1800: # because of GetGeoTransform(can_return_null)
        print('ERROR: Python bindings of GDAL 1.8.0 or later required')
        sys.exit(1)

    sys.exit(main(sys.argv))
