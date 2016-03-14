#!/usr/bin/python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  Name: create_IAU2000_WKT_v2.py
#  Author: Trent Hare
#  Original: Jan 2006
# Feb 2016:
#---- update to report IAU Mean from reports,
#---- Asteroids and IAU reported Comets,
#---- and two new projections (Mollweide and Robinson)
# March 2016:
#---- added IAU authority, cleaned code, added refs and updated albers to stndPar_1,2=60,20
#
#  Description: This Python script creates a IAU2000/2009 WKT projection strings for WMS services
#
# License: Public Domain
#
# INPUT: (naifcodes_radii_m_wAsteroids_IAU2000.csv or naifcodes_radii_m_wAsteroids_IAU2009.csv)
#
# Example file format:
# Naif_id,Body,IAU2000_Mean,IAU2000_Semimajor,IAU2000_Axisb,IAU2000_Semiminor
# 199,Mercury,2439700.00,2439700.00,2439700.00,2439700.00
# 299,Venus,6051800.00,6051800.00,6051800.00,6051800.00
# 399,Earth,6371000.00,6378140.00,6378140.00,6356750.00
# 301,Moon,1737400.00,1737400.00,1737400.00,1737400.00
# 499,Mars,3389500.00,3396190.00,3396190.00,3376200.00
# 401,Phobos,11100.00,13400.00,11200.00,9200.00
# 402,Deimos,6200.00,7500.00,6100.00,5200.00
#...
#
# OUTPUT:
#   Example: WMS#,,GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.8944472236118]],PRIMEM["Reference_Meridian",0],UNIT["Decimal_Degree",0.0174532925199433],AUTHORITY["IAU2000","49900"]]
#
#------------------------------------------------------------------------------
#
#

import os
import sys
import math
import string


def isInt(string):
    is_int = 1
    try:
        int(string)
    except:
        is_int = 0
    return is_int


def main(argv):
    usage = "usage: python %s naifcodes_radii_m_wAsteroids_IAU2000.csv [output.wtk] " % os.path.basename(sys.argv[0])

    if len(sys.argv) < 2:
        print usage
    else:
        inputTable = sys.argv[1]
        # This sets the default to stdout if no file name is passed in.
        fileToOutput = sys.stdout

        # grab year from file name
        theYear = sys.argv[1].split('IAU')[1].split('.')[0]
        if not isInt(theYear):
            print "Can't parse the year from filename: " + sysargv[2]
            print usage
            sys.exit()

        if len(sys.argv) > 2:
            fileToOutput = open(sys.argv[2], 'w')
            print "outfile = %s" % (sys.argv[2])

        #References - block of text for start of files
        refs2000 = """#IAU2000 WKT Codes
# This file derived from the naif ID Codes.txt file distributed by 
# USGS for NASA/IAU/NAIF (http://naif.jpl.nasa.gov/)
#
# 
#     The sources for the constants listed in this file are:
#
#        [1]   Seidelmann, P.K., Abalakin, V.K., Bursa, M., Davies, M.E.,
#              Bergh, C. de, Lieske, J.H., Oberst, J., Simon, J.L.,
#              Standish, E.M., Stooke, P., and Thomas, P.C. (2002).
#              "Report of the IAU/IAG Working Group on Cartographic
#              Coordinates and Rotational Elements of the Planets and
#              Satellites: 2000," Celestial Mechanics and Dynamical
#              Astronomy, v.82, Issue 1, pp. 83-111.
#
"""
        refs2009 = """#IAU2009 WKT Codes
# This file derived from the naif ID Codes.txt file distributed by 
# USGS for NASA/IAU/NAIF (http://naif.jpl.nasa.gov/)
#
# 
#     The sources for the constants listed in this file are:
#
#        [1]   Archinal, B. A., M. F. A'Hearn, E. Bowell, A. Conrad, 
#               G. J. Consolmagno, R. Courtin, T. Fukushima, D. Hestroffer, 
#               J. L. Hilton, G. A. Krasinsky, G. Neumann, J. Oberst, 
#               P. K. Seidelmann, P. Stooke, D. J. Tholen, P. C. Thomas, 
#               I. P. Williams (2011), "Report of the IAU/IAG Working Group
#              on Cartographic Coordinates and Rotational Elements of the 
#              Planets and Satellites: 2011," Celestial Mechanics and Dynamical
#              Astronomy, v.109, Issue 2, pp. 101-135.
#
"""
        if (theYear == "2000"):
            fileToOutput.write(refs2000)
        elif (theYear == "2009"):
            fileToOutput.write(refs2009)
        else:
            print "Warning: No reference for the this year: " + theYear

        for line in open(inputTable):
            tokens = line.split(',')
            # Then Radii values exist in input table
            if tokens[2].replace(" ", "") != "":
                if isInt(tokens[0]):  # is Naif number?
                    theNaifNum = int(tokens[0])
                    theTarget = tokens[1]
                    theMean = float(tokens[2])
                    theA = float(tokens[3])
                    theB = float(tokens[4])
                    theC = float(tokens[5])

                    # Check to see if the Mean should be used, for traxial
                    # bodies
                    if theA != theB and theA != theC:
                        theA = theMean
                        theC = theMean

                    flattening = ((theA - theC) / theA)
                    output = "%i"
                    if flattening <> 0:
                        flattening = 1 / flattening
                        output = "%.13f"

                    #Even = Areocentric
                    #Odd = Areographic

                    # GEOIDS
                    theStr = "#IAU%s WKT Codes for %s\n" % (theYear, theTarget)
                    fileToOutput.write( theStr )

                    gisCode = theNaifNum * 100
                    theStr = "%r,GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 1
                    theStr = "%r,GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    theStr = "\n"
                    #fileToOutput.write( theStr )

                    # Static Projections
                    gisCode = theNaifNum * 100 + 10  # Equirectangular, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 11  # Equirectangular, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 12  # Equirectangular, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 13  # Equirectangular, ographic, clon=180
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 14  # Sinusoidal, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 15  # Sinusoidal, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 16  # Sinusoidal, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 17  # Sinusoidal, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 18  # North Polar, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_North_Pole_Stereographic\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 19  # North Polar, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_North_Pole_Stereographic\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 20  # South Polar, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_South_Pole_Stereographic\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",-90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 21  # South Polar, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_South_Pole_Stereographic\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",-90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 22  # Mollweide, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 23  # Mollweide, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 24  # Mollweide, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 25  # Mollweide, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 26  # Robinson, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 27  # Robinson, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 28  # Robinson, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 29  # Robinson, ocentric, clon=180
                    theStr = "%r,PROJCS[\"%s_Sinusoidal\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",180],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    theStr = "\n"
                    #fileToOutput.write( theStr )

                    # AUTO Projections
                    gisCode = theNaifNum * 100 + 60  # Sinusoidal, ocentric
                    theStr = "%r,PROJCS[\"%s_Sinusoidal_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 61  # Sinusoidal, ographic
                    theStr = "%r,PROJCS[\"%s_Sinusoidal_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 62  # Stereographic, ocentric, clon=0
                    theStr = "%r,PROJCS[\"%s_Stereographic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 63  # Stereographic, ographic, clon=0
                    theStr = "%r,PROJCS[\"%s_Stereographic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Stereographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",1],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 64  # Transverse Mercator, ocentric
                    theStr = "%r,PROJCS[\"%s_Transverse_Mercator_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 65  # Transverse Mercator, ographic
                    theStr = "%r,PROJCS[\"%s_Transverse_Mercator_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 66  # Orthographic, ocentric
                    theStr = "%r,PROJCS[\"%s_Orthographic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Orthographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Longitude_Of_Center\",0.0],PARAMETER[\"Latitude_Of_Center\",90.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 67  # Orthographic, ographic
                    theStr = "%r,PROJCS[\"%s_Orthographic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Orthographic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Longitude_Of_Center\",0.0],PARAMETER[\"Latitude_Of_Center\",90.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 68  # Equidistant_Cylindrical, ocentric
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 69  # Equidistant_Cylindrical, ographic
                    theStr = "%r,PROJCS[\"%s_Equidistant_Cylindrical_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Equidistant_Cylindrical\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 70  # Lambert_Conformal_Conic, ocentric
                    theStr = "%r,PROJCS[\"%s_Lambert_Conformal_Conic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Lambert_Conformal_Conic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",-20],PARAMETER[\"Standard_Parallel_2\",20],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 71  # Lambert_Conformal_Conic, ographic
                    theStr = "%r,PROJCS[\"%s_Lambert_Conformal_Conic_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Lambert_Conformal_Conic\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",-20],PARAMETER[\"Standard_Parallel_2\",20],PARAMETER[\"Latitude_Of_Origin\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 72  # Lambert_Azimuthal_Equal_Area, ocentric
                    theStr = "%r,PROJCS[\"%s_Lambert_Azimuthal_Equal_Area_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Lambert_Azimuthal_Equal_Area\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Latitude_Of_Origin\",90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 73  # Lambert_Azimuthal_Equal_Area, ographic
                    theStr = "%r,PROJCS[\"%s_Lambert_Azimuthal_Equal_Area_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Lambert_Azimuthal_Equal_Area\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Latitude_Of_Origin\",90],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 74  # Mercator, ocentric
                    theStr = "%r,PROJCS[\"%s_Mercator_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mercator\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 75  # Mercator, ographic
                    theStr = "%r,PROJCS[\"%s_Mercator_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mercator\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],PARAMETER[\"Standard_Parallel_1\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 76  # Albers, ocentric
                    theStr = "%r,PROJCS[\"%s_Albers_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0.0],PARAMETER[\"Standard_Parallel_1\",60.0],PARAMETER[\"Standard_Parallel_2\",20.0],PARAMETER[\"Latitude_Of_Origin\",40.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 77  # Albers, ographic
                    theStr = "%r,PROJCS[\"%s_Albers_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0.0],PARAMETER[\"Standard_Parallel_1\",60.0],PARAMETER[\"Standard_Parallel_2\",20.0],PARAMETER[\"Latitude_Of_Origin\",40.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 78  # Oblique Cylindrical Equal Area, ocentric
                    theStr = "%r,PROJCS[\"%s_Oblique_Cylindrical_Equal_Area_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Oblique_Cylindrical_Equal_Area\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0.0],PARAMETER[\"Standard_Parallel_1\",0.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 79  # Oblique Cylindrical Equal Area, ographic
                    theStr = "%r,PROJCS[\"%s_Oblique_Cylindrical_Equal_Area_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Oblique_Cylindrical_Equal_Area\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0.0],PARAMETER[\"Standard_Parallel_1\",0.0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 80  # Mollweide, ocentric
                    theStr = "%r,PROJCS[\"%s_Mollweide_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 81  # Mollweide, ographic
                    theStr = "%r,PROJCS[\"%s_Mollweide_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Mollweide\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    gisCode = theNaifNum * 100 + 82  # Robinson, ocentric
                    theStr = "%r,PROJCS[\"%s_Robinson_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)
                    gisCode = theNaifNum * 100 + 83  # Robinson, ographic
                    theStr = "%r,PROJCS[\"%s_Robinson_AUTO\",\"GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Decimal_Degree\",0.0174532925199433]],PROJECTION[\"Robinson\"],PARAMETER[\"False_Easting\",0],PARAMETER[\"False_Northing\",0],PARAMETER[\"Central_Meridian\",0],UNIT[\"Meter\",1],AUTHORITY[\"IAU%s\",\"%r\"]]\n" % (
                        gisCode, theTarget, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

    if len(sys.argv) > 2:
        fileToOutput.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
