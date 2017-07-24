#!/usr/bin/python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  Name: create_PostGIS_IAU2000_wkt_proj4_INSERT.py
#  Author: Trent Hare
#  Original: Jan 2006
# Feb 2016:
#---- update to report IAU Mean from reports,
#---- Asteroids and IAU reported Comets,
#---- and two new projections (Mollweide and Robinson)
# March 2016:
#---- added IAU authority, cleaned code, added refs and updated albers to stndPar_1,2=60,20
# July 2016:
#---- changed Decimal_Degree to just Degree
#July 2017:
#---- Updated for Python v3 and support for -1 NoData values in table
#
#  Description: This Python script creates a IAU2000 Proj4 for PostGIS services
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
#   WMS Example: ,GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.8944472236118]],PRIMEM["Reference_Meridian",0],UNIT["Degree",0.0174532925199433],AUTHORITY["IAU2000","49900"]]
#   Proj 4 Example: +proj=longlat +a=3396190 +b=3376200 +no_defs
#
#------------------------------------------------------------------------------
#
#

import os
import sys

def isInt(string):
    is_int = 1
    try:
        int(string)
    except:
        is_int = 0
    return is_int


def main(argv):
    usage = "usage: python %s naifcodes_radii_m_wAsteroids_IAU2000.csv [output.proj4] " % os.path.basename(sys.argv[
                                                                                                           0])

    if len(sys.argv) < 2:
        print(usage)
    else:
        inputTable = sys.argv[1]
        # This sets the default to stdout if no file name is passed in.
        fileToOutput = sys.stdout

        # grab year from file name
        theYear = sys.argv[1].split('IAU')[1].split('.')[0]
        if not isInt(theYear):
            print("Can't parse the year from filename: " + sys.argv[2])
            print(usage)
            sys.exit()

        if len(sys.argv) > 2:
            fileToOutput = open(sys.argv[2], 'w')
            print ("outfile = %s" % (sys.argv[2]))

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
#              G. J. Consolmagno, R. Courtin, T. Fukushima, D. Hestroffer, 
#              J. L. Hilton, G. A. Krasinsky, G. Neumann, J. Oberst, 
#              P. K. Seidelmann, P. Stooke, D. J. Tholen, P. C. Thomas, 
#              I. P. Williams (2011), "Report of the IAU/IAG Working Group
#              on Cartographic Coordinates and Rotational Elements of the 
#              Planets and Satellites: 2011," Celestial Mechanics and Dynamical
#              Astronomy, v.109, Issue 2, pp. 101-135.
#
"""
        #if (theYear == "2000"):
        #    fileToOutput.write(refs2000)
        #elif (theYear == "2009"):
        #    fileToOutput.write(refs2009)
        #else:
        #    print "Warning: No reference for the this year: " + theYear

        for line in open(inputTable):
            tokens = line.split(',')
            # Then Radii values exist in input table
            if (tokens[2].replace(" ", "") != "") \
                and (tokens[2].replace(" ", "") != "-1"):
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
                    if (flattening != 0):
                        flattening = 1 / flattening

                    #Even = Areocentric
                    #Odd = Areographic

                    gisCode = theNaifNum * 100

                    # Delete existing EPSG code - if exists
                    theStr = "DELETE FROM spatial_ref_sys WHERE srid IN (%r);\n" % (
                        gisCode)
                    fileToOutput.write(theStr)

                    #theStr = tokens[1]+" ,"+str(gisCode)+", +proj=longlat +a=%r +b=%r +no_defs\n" % (float(tokens[2]),float(tokens[4]))
                    # INSERT statement
                    theStr = "INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) VALUES (%r, 'IAU%s', %r, " % (
                        gisCode, theYear, gisCode)
                    fileToOutput.write(theStr)

                    # WKT
                    theStr = "%r,GEOGCS[\"%s %s\",DATUM[\"D_%s_%s\",SPHEROID[\"%s_%s_IAU_IAG\",%r,%r]],PRIMEM[\"Reference_Meridian\",0],UNIT[\"Degree\",0.0174532925199433],AUTHORITY[\"IAU%s\",\"%r\"]]," % (
                        gisCode, theTarget, theYear, theTarget, theYear, theTarget, theYear, theA, flattening, theYear, gisCode)
                    fileToOutput.write(theStr)

                    # proj4
                    #+proj=longlat +a=3396190 +b=3376200 +no_defs
                    theStr = "'+proj=longlat +a=%r +b=%r +no_defs');\n" % (
                        theA, theC)
                    fileToOutput.write(theStr)

    if len(sys.argv) > 2:
        fileToOutput.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
