#!/usr/bin/env python3
###############################################################################
#_TITLE  isis3_to_pds4_LOLA_pysis.py
#
#_ARGS
#   input.cub
#   output_config.txt
#
#_REQUIRES
#        Python 3.x
#        pysis library: https://github.com/wtolson/pysis (for install see page)
#        --recommended Anaconda Python 3.x environment w/ gdal, once installed:
#        $ conda install -c conda-forge gdal 
#
#_DESC
#        Create a configuration for a pds4 conversion using gdal_translate.
#        Requires an existing PDS4 XML template with known variables.
#        The default PDS4 template for GDAL is available in GDAL_DATA
#        https://trac.osgeo.org/gdal/wiki/FAQInstallationAndBuilding#WhatisGDAL_DATAenvironmentvariable
#
#_HIST
#        Oct 18 2017 - Trent Hare (thare@usgs.gov) - original version
#
#_LICENSE
#        Public domain (unlicense)
#   
#_END
##############################################################################
import sys, os
#import pysis
from pysis.isis import getkey
import gdal

def Usage(theApp):
    print( 'Usage:\npython {} input.cub output.config'.format(theApp))
    print( '   optional: to run gdal_translate send: -run')
    print( '   optional: to set a PDS4 XML template send: -template my.xml')
    print( '      by default the template used is from $GDALDATA/pds4_template.xml')
    print( '\nUsage: {} -run -template myTemplate.xml in.cub out.config'.format(theApp))
    print( 'Note: Requires an existing PDS4 XML template with known variables.\n')
    sys.exit(1)

def EQUAL(a, b):
    return a.lower() == b.lower()

#/************************************************************************/
#/*                                main()                                */
#/************************************************************************/
def main( argv = None ):

    inputlbl = None
    outputConfig = None
    run = None
    template = None

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

        if EQUAL(argv[i], '-run'):
            run = True
        elif EQUAL(argv[i], '-template'):
            i = i + 1
            template = argv[i]
        elif inputlbl is None:
            inputlbl = argv[i]
        elif outputConfig is None:
            outputConfig = argv[i]
        else:
            return Usage(argv[0])
        i = i + 1

    if inputlbl is None:
        return Usage(argv[0])
    if outputConfig is None:
        return Usage(argv[0])
    if template is None:
        template = 'pds4_template.xml'

    #open output config file
    fileConfig = open(outputConfig, 'w')
    print('writing {}'.format(outputConfig))

    #Write first comment line
    theLine = '#{0} {1} {2}\n'.format(sys.argv[0], sys.argv[1], sys.argv[2])
    fileConfig.write(theLine)

    #Next lines are not available in ISIS3 label
    theLine = '-co VAR_TARGET_TYPE=Satellite\n'
    fileConfig.write(theLine)

    theLine = '-co VAR_INVESTIGATION_AREA_LID_REFERENCE="urn:nasa:pds:context:instrument_host:spacecraft.lro"\n'
    fileConfig.write(theLine)

    try:
        target = getkey(from_=inputlbl, keyword='TargetName', grp='Mapping')
        theLine = '-co VAR_TARGET={}'.format(target)
        fileConfig.write(theLine)
    except KeyError:
        print('No Target in ISIS3 Label')

    try:
        mission = getkey(from_=inputlbl, keyword='InstrumentHostName', grp='Archive')
        theLine = '-co VAR_INVESTIGATION_AREA_NAME="{}"\n'.format(mission.rstrip())
        fileConfig.write(theLine)
    except KeyError:
        print('No InstrumentHostName in ISIS3 Label')

    try:
        dataSetID = getkey(from_=inputlbl, keyword='DataSetId', grp='Archive')
        theLine = '-co VAR_LOGICAL_IDENTIFIER={}'.format(dataSetID)
        fileConfig.write(theLine)
    except KeyError:
        print('No DataSetId in ISIS3 Label')

    try:
        observeID = getkey(from_=inputlbl, keyword='InstrumentId', grp='Archive')
        theLine = '-co VAR_OBSERVING_SYSTEM_NAME={}'.format(observeID)
        fileConfig.write(theLine)
    except KeyError:
        print('No InstrumentId in ISIS3 Label')

    try:
        fileName = getkey(from_=inputlbl, keyword='ProductId', grp='Archive')
        theLine = '-co VAR_TITLE={}'.format(fileName)
        fileConfig.write(theLine)
    except KeyError:
        print('No ProductId in ISIS3 Label')

    fileConfig.close()

    #write out helper line for gdal - can run from here too
    outPDS4 = inputlbl.replace('.cub','_pds4.xml')

    theCmd='gdal_translate -of PDS4 -co IMAGE_FORMAT=GEOTIFF -co TEMPLATE={0} --optfile {1} {2} {3}'.format(template, outputConfig, inputlbl, outPDS4)

    if run is None:
        print('\nRecommended gdal run:')
        print('{}\n'.format(theCmd))
    else: #run gdal
        os.system(theCmd)


if __name__ == '__main__':
    #version_num = int(gdal.VersionInfo('VERSION_NUM'))
    #if version_num < 2200: # because of PDS4 support
    #    print('ERROR: Python bindings of GDAL 2.2.0 or later required')
    #    sys.exit(1)

    sys.exit(main(sys.argv))

