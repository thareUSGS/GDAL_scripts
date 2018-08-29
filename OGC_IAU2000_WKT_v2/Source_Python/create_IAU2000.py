#!/usr/bin/python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  Name: create_IAU2000_WKT_v3.py
#  Author: Trent Hare, Jean-Christophe Malapert
#  Original: Jan 2006
# Feb 2016:
# ---- update to report IAU Mean from reports,
# ---- Asteroids and IAU reported Comets,
# ---- and two new projections (Mollweide and Robinson)
# March 2016:
# ---- added IAU authority, cleaned code, added refs and updated albers to stndPar_1,2=60,20
# July 2016:
# ---- changed Decimal_Degree to just Degree
# Sep 2016:
# ---- Removed extra " before GEOGCS in map projected string
# July 2017:
# ---- Updated for Python v3 and support for -1 NoData values in table
# Aug 2018:
# ---- Updated for 2015 IAU report and change 2009 to IAU from IAU_IAG
# ---- Code refactoring (logging, class, enumerations, removed repetition of WKT string, command line parser)
# ---- Added creation capabilities for prj and iniFile for proj4
# ---- Added rotation direction consideration for ocentric and ographic CRS
# ---- Improved WKT (towgs84 string for datum shifting)
# ---- Fixed bug about projection parameter (Fully compliant with gdal)
# ---- Fixed bug about Halley WKT (radius was -1)
# ---- Changed algorithm for triaxial ellipsoids
# ---- Added WKT validation
#
#
#  Description: This Python script creates a IAU2000/2009/2015 WKT projection strings for WMS services. prj and
#               initFile for proj4 can be created
#
# License: Public Domain
#
# INPUT: (naifcodes_radii_m_wAsteroids_IAU2000.csv or naifcodes_radii_m_wAsteroids_IAU2015.csv)
#
# Example file format:
# Naif_id,Body,IAU2015_Mean,IAU2015_Semimajor,IAU2015_Axisb,IAU2015_Semiminor,rotation,origin_long_name,origin_lon_pos
# 10,Sun,695700000.00,695700000.00,695700000.00,695700000.00,Direct,,
# 199,Mercury,2439400.00,2440530.00,2440530.00,2438260.00,Direct,Hun Kal,20
# 299,Venus,6051800.00,6051800.00,6051800.00,6051800.00,Retrograde,Ariadne,0
# 399,Earth,6371008.40,6378136.60,6378136.60,6356751.90,Direct,Greenwich,0
# 301,Moon,1737400.00,1737400.00,1737400.00,1737400.00,Direct,,
# 499,Mars,3389500.00,3396190.00,3396190.00,3376200.00,Direct,Airy-0,0
# 401,Phobos,11080.00,13000.00,11400.00,9100.00,Direct,,
# 402,Deimos,6200.00,7800.00,6000.00,5100.00,Direct,,
# ...
#
# OUTPUT:
#   Example: WMS#,GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.8944472236118]],PRIMEM["Reference_Meridian",0],UNIT["Degree",0.0174532925199433],AUTHORITY["IAU2000","49900"]]
#
# ------------------------------------------------------------------------------
#
#

import os
import sys
import re
import subprocess
from enum import Enum
import logging
import argparse
import time
import functools

try:
    import coloredlogs
except:
    print("please install coloredlogs package to get logs in color")

assert sys.version_info >= (2, 7), "Install python version >= 2.7"


class WKT:
    """
    Class that allows to build a simple WKT.

    Constants
    ---------
    GEOGRS: WKT template for a CRS based on longitude/latitude
    PROJCS : WKT template for Porjected CRS

    """
    GEOGRS = "GEOGCS[\"%s\"," \
             "DATUM[\"%s\"," \
             "SPHEROID[\"%s\",%r,%r]," \
             "TOWGS84[0,0,0]" \
             "]," \
             "PRIMEM[\"%s\",%s]," \
             "UNIT[\"Degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]]," \
             "%s" \
             "AUTHORITY[\"%s\",\"%s\"]" \
             "]"

    PROJCS = "PROJCS[\"%s\"," \
             "%s," \
             "%s" \
             "]"

    def __init__(self, geogcsName, datumName, sphereoidName, radius, inverseFlattening, authorityName, authorityCode):
        """
        Creates a new WKT that describes a CRS based on longitude/latitude coordinates

        The WKT representing a CRS based on longitude/latitude is displayed as follow:
        GEOGCS["<geogcsName>",
           DATUM["<datumName>",
                SPHEROID["<sphereoidName>",<radius>,<inverseFlattening>]
                TOWGS84[0,0,0]
           ],
           PRIMEM["<longitudeName>",<longitudePos>],
           UNIT["Degree",0.0174532925199433,
                AUTHORITY["EPSG","9122"]
           ],
           <axis order>
           AUTHORITY["<authorityName>","<authorityCode>"]
        ]

        For planets, satellites and dwarf planets, IAU defined the North Pole of a planet to be that axis of rotation
        which lies north of the solar system's invariable plane. Which means that is possible for bodies to rotate
        retrograde.
        When  <axis order> is not defined, longitude is counted positvely to East for ographic CRS : this means all
        bodies having a retrograde rotation.  When planet rotates to direct, <axis order> must be defined with longitude
        positive to West for ographic CRS. The rotation direction can be defined by ``setLongitudeAxis`` method.
        Sun, Earth and Moon are the exception to this rule because their rotation is direct but the longitude is counted
        positively to East for ographic CRS.
        For ocentric CRS, the mathematical convention for spherical coordinates is applied : the longitude is always
        counted positively to East.

        For a projected CRS, the WKT is displayed as follow:
        PROJCS["<projectionName>",
            <GEOGCS>
            <projection parameters>
        ]

        <projection parameters> are defined in the WKT.Projection class.
        The projection can be set in setProjection method

        :param geogcsName: the CRS name
        :param datumName: the datum name
        :param sphereoidName: the spheroid name
        :param radius: the radius in meter
        :param inverseFlattening: the inverseFlattening or 0 for a sphere
        :param authorityName: the authority name that is responsible of defining this kiond of CRS
        :param authorityCode: the authority code that identifies this CRS in the authority name namespace
        :type geogcsName: str
        :type datumName: str
        :type sphereoidName: str
        :type radius: float
        :type inverseFlattening: float
        :type authorityName: str
        :type authorityCode: str

        .. seealso:: setLongitudeAxis(), setProjection()
        """

        if 'logger' in globals():
            # ok logger is defined, we can log event
            pass
        else:
            # logger is not defined, we define it and we make it disabled
            global logger
            logger = logging.getLogger()
            logger.disabled = True

        logger.debug("Entering in constructor with geogcsName=%s, datumName=%s, sphereoidName=%s, radius=%s, "
                     "inverseFlattening=%s, authorityName=%s, authorityCode=%s" % (
                         geogcsName, datumName, sphereoidName, radius, inverseFlattening, authorityName, authorityCode
                     ))

        assert isinstance(geogcsName, str), "WKT.__init__: geogcsName must be a string for geogcsName=%s" % geogcsName
        assert isinstance(datumName, str), "WKT.__init__: datumName must be a string for geogcsName=%s" % geogcsName
        assert isinstance(sphereoidName,
                          str), "WKT.__init__: sphereoidName must be a string for geogcsName=%s" % geogcsName
        assert isinstance(radius,
                          (int, float)), "WKT.__init__: radius must be an int ot float for geogcsName=%s" % geogcsName
        assert radius > 0, "WKT.__init__: radius=%s, it must be > 0 for geogcsName=%s" % (radius, geogcsName)
        assert isinstance(inverseFlattening, (
            float, int)), "WKT.__init__: inverseFlattening must be a string for geogcsName=%s" % geogcsName
        # TODO : flattening could be negative, is it OK ?
        # look to 1000041,Hartley 2,580.00,340.00,1160.00,1160.00,,,
        #assert inverseFlattening >= 0, "WKT.__init__: inverseFlattening=%s, it must be >=0 for geogcsName=%s"%(inverseFlattening,geogcsName)
        assert isinstance(authorityName,
                          str), "WKT.__init__: authorityName must be a string for geogcsName=%s" % geogcsName
        assert isinstance(authorityCode,
                          str), "WKT.__init__: authorityCode must be a string for geogcsName=%s" % geogcsName
        self.__geogcsName = geogcsName
        self.__datumName = datumName
        self.__sphereoidName = sphereoidName
        self.__radius = radius
        self.__inverseFlattening = inverseFlattening
        self.__authorityName = authorityName
        self.__authorityCode = authorityCode
        self.__projection = None
        self.__projectionName = None
        self.__projectionAuthorityName = None
        self.__projectionAutorityCode = None
        self.__longitudeAxisOrder = None  # when None means East
        self.__longitudeName = 'Reference_Meridian'
        self.__longitudePos = 0.0

        logger.debug("Exiting from constructor")

    class ValidationError(Exception):
        """Raised when gdalsrsinfo returns an error"""
        pass

    class CRS(Enum):
        OCENTRIC = "Ocentric"
        OGRAPHIC = "Ographic"
        PROJECTED_OCENTRIC = "Projected ocentric"
        PROJECTED_OGRAPHIC = "Projected ographic"

    class LongitudeAxis(Enum):
        """Enumerated class to show if the longitude is counted positively to West/East"""
        WEST = "WEST"
        EAST = "EAST"

    class Projection(Enum):
        """List of supported projections.

        It exists two kind of projections :
        - the classical ones
        - the auto that allow the user to also submit the projection parameters

        Each projection value is a hash that contains:
        - code for ocentric CRS
        - url of the projection
        - the projection name
        - the projection parameters

        """
        EQUIRECTANGULAR_0 = {  # Equirectangular, clon=0
            "code": 10,
            "url": "https://proj4.org/operations/projections/eqc.html",
            "projection": "Equirectangular",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "latitude_Of_Origin": 0
            }
        }
        EQUIRECTANGULAR_180 = {  # Equirectangular, clon=180
            "code": 12,
            "url": "https://proj4.org/operations/projections/eqc.html",
            "projection": "Equirectangular",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 180,
                "Latitude_Of_Origin": 0
            }
        }
        SINUSOIDAL_0 = {  # Sinusoidal, clon=0
            "code": 14,
            "url": "https://proj4.org/operations/projections/sinu.html",
            "projection": "Sinusoidal",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 0
            }
        }
        SINUSOIDAL_180 = {  # Sinusoidal, clon=180
            "code": 16,
            "url": "https://proj4.org/operations/projections/sinu.html",
            "projection": "Sinusoidal",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 180
            }
        }
        STEREOGRAPHIC_NORTH = {  # North Polar, clon=0
            "code": 18,
            "url": "https://proj4.org/operations/projections/stere.html",
            "projection": "Stereographic",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Scale_Factor": 1,
                "Latitude_Of_Origin": 90
            }
        }
        STEREOGRAPHIC_SOUTH = {  # South Polar, clon=0
            "code": 20,
            "url": "https://proj4.org/operations/projections/stere.html",
            "projection": "Stereographic",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Scale_Factor": 1,
                "Latitude_Of_Origin": -90
            }
        }
        MOLLWEIDE_0 = {  # Mollweide, clon=0
            "code": 22,
            "url": "https://proj4.org/operations/projections/moll.html",
            "projection": "Mollweide",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0
            }
        }
        MOLLWEIDE_180 = {  # Mollweide, clon=180
            "code": 24,
            "url": "https://proj4.org/operations/projections/moll.html",
            "projection": "Mollweide",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 180
            }
        }
        ROBINSON_0 = {  # Robinson, clon=0
            "code": 26,
            "url": "https://proj4.org/operations/projections/robin.html",
            "projection": "Robinson",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 0
            }
        }
        ROBINSON_180 = {  # Robinson, clon=180
            "code": 28,
            "url": "https://proj4.org/operations/projections/robin.html",
            "projection": "Robinson",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 180
            }
        }
        AUTO_SINUSOIDAL = {  # Auto Sinusoidal
            "code": 60,
            "url": "https://proj4.org/operations/projections/sinu.html",
            "projection": "Sinusoidal",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 0
            }
        }
        AUTO_STEREOGRAPHIC = {  # Auto Stereographic, clon=0
            "code": 62,
            "url": "https://proj4.org/operations/projections/stere.html",
            "projection": "Stereographic",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Scale_Factor": 1,
                "Latitude_Of_Origin": 0
            }
        }
        AUTO_TRANSVERSE_MERCATOR = {  # Auto Transverse Mercator
            "code": 64,
            "url": "https://proj4.org/operations/projections/tmerc.html",
            "projection": "Transverse_Mercator",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Scale_Factor": 0.9996,
                "Latitude_Of_Origin": 0
            }
        }
        AUTO_ORTHOGRAPHIC = {  # Auto Orthographic
            "code": 66,
            "url": "https://proj4.org/operations/projections/ortho.html",
            "projection": "Orthographic",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Latitude_Of_Origin": 90
            }
        }
        AUTO_EQUIRECTANGULAR = {  # Auto Equidistant_Cylindrical
            "code": 68,
            "url": "https://proj4.org/operations/projections/eqc.html",
            "projection": "Equirectangular",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 180,
                "Latitude_Of_Origin": 0
            }
        }
        AUTO_LAMBERT_CONFORMAL_CONIC = {  # Auto Lambert_Conformal_Conic
            "code": 70,
            "url": "https://proj4.org/operations/projections/lcc.html",
            "projection": "Lambert_Conformal_Conic_2SP",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Standard_Parallel_1": -20,
                "Standard_Parallel_2": 20,
                "Latitude_Of_Origin": 0
            }
        }
        AUTO_LAMBERT_AZIMUTHAL_EQUAL = {  # Auto Lambert_Azimuthal_Equal_Area
            "code": 72,
            "url": "https://proj4.org/operations/projections/laea.html",
            "projection": "Lambert_Azimuthal_Equal_Area",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 0,
                "Latitude_Of_Center": 90
            }
        }
        AUTO_MERCATOR = {  # Auto Mercator
            "code": 74,
            "url": "https://proj4.org/operations/projections/merc.html",
            "projection": "Mercator_1SP",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0,
                "Scale_Factor": 1  # TODO : Check this value - transverse mercator is defined to 0.9996
            }
        }
        AUTO_ALBERS = {  # Auto Albers
            "code": 76,
            "url": "https://proj4.org/operations/projections/aea.html",
            "projection": "Albers_Conic_Equal_Area",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_Of_Center": 0.0,
                "Standard_Parallel_1": 60.0,
                "Standard_Parallel_2": 20.0,
                "Latitude_Of_Center": 40.0
            }
        }
        # TODO : AUTO_OBLIQUE_CYLINDRICAL not defined in GDAL 2.2.7 => produce an error
        # It seems it is OK the next GDAL release : https://github.com/OSGeo/gdal/pull/101
        AUTO_OBLIQUE_CYLINDRICAL = {  # Auto Oblique Cylindrical Equal Area -- Problem for this projection
            "code": 78,
            "projection": "Oblique_Cylindrical_Equal_Area",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0.0,
                "Standard_Parallel_1": 0.0
            }
        }
        AUTO_MOLLWEIDE = {  # Auto Mollweide
            "code": 80,
            "url": "https://proj4.org/operations/projections/moll.html",
            "projection": "Mollweide",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Central_Meridian": 0.0
            }
        }
        AUTO_ROBINSON = {  # Auto Robinson
            "code": 82,
            "url": "https://proj4.org/operations/projections/robin.html",
            "projection": "Robinson",
            "parameters": {
                "False_Easting": 0,
                "False_Northing": 0,
                "Longitude_of_center": 0.0
            }
        }

    def setLongitudeAxis(self, longitudeAxis):
        """
        Sets the longitude axis.

        By default the longitude Axis is set to East when it is not defined

        :param longitudeAxis: an enumeration from WKT.LongitudeAxis (WKT.LongitudeAxis.EAST or WKT.LongitudeAxis.WEST)
        :type longitudeAxis: WKT.LongitudeAxis
        """
        logger.debug("Entering in setLongitudeAxis with longitudeAxis=%s" % longitudeAxis)

        assert longitudeAxis == WKT.LongitudeAxis.WEST or longitudeAxis == WKT.LongitudeAxis.EAST
        self.__longitudeAxisOrder = longitudeAxis

        logger.debug("Exiting from setLongitudeAxis")

    def setPrimem(self, longitudeName="Reference_Meridian", longitudePos=0.0):
        """
        Sets the primem meridian

        :param longitudeName: a particular point on the planet that defines a longitude. By default this value is
        set to "Reference_Meridian"
        :param longitudePos: longitude position in decimal degree [0..360] of the longitudeName.
        The longitudePos is defined in the rotation direction of the planet
        :type longitudeName: str
        :type longitudePos: float
        """

        logger.debug("Entering in setPrimem with longitudeName=%s, longitudePos=%s" % (longitudeName, longitudePos))

        assert isinstance(longitudeName, str), "WKT.setPrimem: longitudeName must be a string"
        assert isinstance(longitudePos, (int, float)), "WKT.setPrimem: longitudePos must be a string"
        assert float(longitudePos) <= 360, "WKT.setPrimem: longitudePos=%s. It must be between 0 and 360" % longitudePos
        self.__longitudeName = longitudeName
        self.__longitudePos = longitudePos

        logger.debug("Exiting from setPrimem")

    def setProjection(self, projectionName, projectionEnum, projectionAuthorityName, projectionAuthorityCode):
        """
        Sets the projection

        :param projectionName: projection name
        :param projectionEnum: projection parameters
        :param projectionAuthorityName: name of the responsible for defining the projection
        :param projectionAuthorityCode: ID within the authority name that defines the projection
        :type projectionName: str
        :type projectionEnum: str
        :type projectionAuthorityName: str
        :type projectionAuthorityCode: str
        """

        logger.debug("Entering in setProjection with projectionName=%s, projectionEnum=%s, "
                     "projectionAuthorityName=%s, projectionAuthorityCode=%s" % (
                         projectionName, projectionEnum,
                         projectionAuthorityName, projectionAuthorityCode
                     ))

        assert isinstance(projectionName, str), "WKT.setProjection: projectionName must be a string"
        assert isinstance(projectionEnum,
                          WKT.Projection), "WKT.setProjection: projectionEnum must be a member of Projection"
        assert isinstance(projectionAuthorityName, str), "WKT.setProjection: projectionAuthorityName must be a string"
        assert isinstance(projectionAuthorityCode, str), "WKT.setProjection: projectionAuthorityCode must be a string"
        self.__projection = projectionEnum
        self.__projectionName = projectionName
        self.__projectionAuthorityName = projectionAuthorityName
        self.__projectionAutorityCode = projectionAuthorityCode

        logger.debug("Exiting from setProjection")

    def unsetProjection(self):
        """
        Unsets the projection.
        """

        logger.debug("Entering in unsetProjection")

        self.__projection = None
        self.__projectionName = None
        self.__projectionAuthorityName = None
        self.__projectionAutorityCode = None

        logger.debug("Existing from unsetProjection")

    def __getGeoGrs(self):
        """
        Returns the CRS based on longitude/latitude

        :return: the WKT
        :rtype: str
         """

        logger.debug("Entering in __getGeoGrs")

        if self.__longitudeAxisOrder is None or self.__longitudeAxisOrder == WKT.LongitudeAxis.EAST:
            # if no rotation is defined, then ocentric CRS is used => longitude is positive to EAST
            # When no axis is defined, it means longitude is positive to EAST
            axis = ""
        else:
            axis = "AXIS[\"latitude\",NORTH],AXIS[\"longitude\",%s]," % self.__longitudeAxisOrder.value

        # building WKT string
        wkt = WKT.GEOGRS % (
            self.__geogcsName, self.__datumName, self.__sphereoidName, self.__radius, self.__inverseFlattening,
            self.__longitudeName, self.__longitudePos, axis, self.__authorityName, self.__authorityCode
        )

        logger.debug("Exiting from __getGeoGrs")
        return wkt

    def __getProJcs(self):
        """
        Returns the projected CRS.

        :return: the WKT
        :rtype: str
        """

        logger.debug("Entering in __getProJcs")

        # defines the projection name in the WKT
        projParams = "PROJECTION[\"" + self.__projection.value["projection"] + "\"]"

        # defines the projection parameters in the WKT
        for param in self.__projection.value['parameters'].keys():
            projParams += ",PARAMETER[\"%s\",%r]" % (param, self.__projection.value['parameters'][param])

        # defines the projection authority
        projParams += ",UNIT[\"Meter\",1, AUTHORITY[\"EPSG\",\"9001\"]],AUTHORITY[\"%s\",\"%s\"]" % (
            self.__projectionAuthorityName, self.__projectionAutorityCode)

        # building WKT
        wkt = WKT.PROJCS % (
            self.__projectionName, self.__getGeoGrs(), projParams
        )

        logger.debug("Exiting from __getProJcs")
        return wkt

    def getWkt(self):
        """
        Returns the WKT

        :return: the WKT
        :rtype: str

        :Example: WKT based on a CRS longitude/latitude
        >>> wkt = WKT("unnamed ellipse","unknown","unnamed",60000,12,"unnamed authority","unnamed code")
        >>> wkt.getWkt()
        'GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",60000,12]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["unnamed authority","unnamed code"]]'


        :Example: WKT based on a projectedCRS
        >>> wkt = WKT("unnamed ellipse","unknown","unnamed",60000,12,"unnamed authority","unnamed code")
        >>> wkt.setProjection("unnamed projection", WKT.Projection.EQUIRECTANGULAR_0,"unnamed authority proj","unnamed authority code proj")
        >>> wkt.getWkt()
        'PROJCS["unnamed projection",GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",60000,12]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["unnamed authority","unnamed code"]],PROJECTION["Equirectangular"],PARAMETER["False_Easting",0],PARAMETER["Standard_Parallel_1",0],PARAMETER["Central_Meridian",180],PARAMETER["False_Northing",0],UNIT["Meter",1, AUTHORITY["EPSG","9001"]],AUTHORITY["unnamed authority proj","unnamed authority code proj"]]'
        """

        logger.debug("Entering in getWkt")

        if self.__projectionName is not None:
            # Use projected CRS when a projection is defined
            result = self.__getProJcs()
        else:
            # Use Geo CRS when no projection is defined
            result = self.__getGeoGrs()

        logger.debug("Exiting from getWkt")
        return result

    @staticmethod
    def __fixWKTforProj4(wkt, proj4):
        """
        Fix WKT and proj4 string
        :param wkt: WKT
        :param proj4: proj4
        :return: list of wkt,proj4
        """
        assert isinstance(wkt, str), "WKT.__fixWKTforProj4: wkt must be a string"
        assert isinstance(proj4, str), "WKT.__fixWKTforProj4: proj4 must be a string"
        if wkt.rfind('AXIS["longitude",WEST]') != -1:
            posNoDefs = proj4.rfind("+no_defs")
            newProj4 = proj4[0:posNoDefs]+"+axis=wnu "+proj4[posNoDefs:len(proj4)]
            extension = "EXTENSION[\"PROJ4\",\"%s\"]," % newProj4
            posAuthority = wkt.rfind('AUTHORITY')
            newWkt = wkt[0:posAuthority]+extension+wkt[posAuthority:len(wkt)]
        else:
            newWkt = wkt
            newProj4 = proj4

        return [newWkt, newProj4]

    @staticmethod
    def isValid(wkt):
        """Returns [True,projString, wkt] when the WKT is valid otherwise [False,None]

        :return: [True,projString, wkt] when the WKT is valid otherwise [False,None]
        :rtype: list
        """

        logger.debug("Entering in isValid")

        assert isinstance(wkt, str), "WKT.isValid: wkt must be a string"
        projString = None
        result = False

        try:
            # Call gdalsrsinfo
            result = subprocess.Popen(['gdalsrsinfo', '-v', wkt], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      encoding='utf8')
            out, err = result.communicate()
            result = "Validate Succeeds" in out
            if result:
                # extracting PROJ.4 string
                m = re.search(".*PROJ.4 : \'(.*)\'.*", out)
                if m:
                    projString = m.group(1)
                    wkt, projString = WKT.__fixWKTforProj4(wkt, projString)
            else:
                if len(err) == 0:
                    err = wkt
                logger.error("WKT is not valid : %s" % err)
        except:
            logger.critical("Please install gdalsrsinfo")

        logger.debug("Exiting from isValid with %s", result)
        return [result, projString, wkt]


class IAUCatalog:
    """
    IAUCatelog processes a CSV file in order to convert it in a interoperable format

    Constants
    ---------
    REFERENCES: Source of CSV file
    """
    # References - block of text for start of files
    REFERENCES = {
        "IAU2000": """#IAU2000 WKT Codes
# This file derived from the naif ID Codes.txt file distributed by
# USGS for NASA/IAU/NAIF (http://naif.jpl.nasa.gov/)
#
#
#     The sources for the constants listed in this file are:
#
#        [1]  Seidelmann, P.K., Abalakin, V.K., Bursa, M., Davies, M.E.,
#              Bergh, C. de, Lieske, J.H., Oberst, J., Simon, J.L.,
#              Standish, E.M., Stooke, P., and Thomas, P.C. (2002).
#              "Report of the IAU/IAG Working Group on Cartographic
#              Coordinates and Rotational Elements of the Planets and
#              Satellites: 2000," Celestial Mechanics and Dynamical
#              Astronomy, v.82, Issue 1, pp. 83-111.
#
""",
        "IAU2009": """#IAU2009 WKT Codes
# This file derived from the naif ID Codes.txt file distributed by
# USGS for NASA/IAU/NAIF (http://naif.jpl.nasa.gov/)
#
#
#     The sources for the constants listed in this file are:
#
#        [2]  Archinal, B. A., M. F. A'Hearn, E. Bowell, A. Conrad,
#              G. J. Consolmagno, R. Courtin, T. Fukushima, D. Hestroffer,
#              J. L. Hilton, G. A. Krasinsky, G. Neumann, J. Oberst,
#              P. K. Seidelmann, P. Stooke, D. J. Tholen, P. C. Thomas,
#              I. P. Williams (2011), "Report of the IAU Working Group
#              on Cartographic Coordinates and Rotational Elements of the
#              Planets and Satellites: 2011," Celestial Mechanics and Dynamical
#              Astronomy, v.109, Issue 2, pp. 101-135.
#
""",
        "IAU2015": """#IAU2015 WKT Codes
# This file derived from the naif ID Codes.txt file distributed by
# USGS for NASA/IAU/NAIF (http://naif.jpl.nasa.gov/)
#
#
#     The sources for the constants listed in this file are:
#
#        [3] Archinal, B. A., C. H. Acton, M. F. A'Hearn, A. Conrad,
#             G. J. Consolmagno, T. Duxbury, D. Hestroffer, J. L. Hilton,
#             R. L. Kirk, S. A. Klioner, D. McCarthy, J. Oberst, J. Ping,
#             P. K. Seidelmann, D. J. Tholen, P. C. Thomas,
#             I. P. Williams (2018), "Report of the IAU Working Group
#             on Cartographic Coordinates and Rotational Elements of the
#             Planets and Satellites: 2015," Celestial Mechanics and Dynamical
#             Astronomy, 130: 22. https://doi.org/10.1007/s10569-017-9805-5.
#
"""
    }

    def __init__(self, file):
        """
        Creates a IAU catalog

        :param file: CSV file
        :type file: str
        """

        if 'logger' in globals():
            # ok logger is debug, we can log event
            pass
        else:
            # logger is not defined, we define it and we make it disabled
            global logger
            logger = logging.getLogger()
            logger.disabled = True

        logger.debug("Entering in constructor with file=%s" % file)

        assert isinstance(file, str), "IAUCatalog.__init__: file must be a string"
        self.__file = file
        self.__theYear = self.__ckeckFileNameAndGetYear(file)

        # Before 2015, the longitude of all CRS was positive to East (this was not conform to IAU definition).
        # In this version, the longitude is conform to IAU definition
        if float(self.__theYear) < 2015:
            raise Exception("This program is not valid before 2015")

        self.__initGroupAndRefsIAU(self.__theYear)

        logger.debug("Exit from constructor")

    def __ckeckFileNameAndGetYear(self, file):
        """
        Checks the filename string and retrieves the year

        The year is used to get the right IAU publication.

        :param file: the filename
        :type file: str
        """
        logger.debug("Entering in __ckeckFileNameAndGetYear with file=%s" % file)

        assert isinstance(file, (str)), "IAUCatalog.__ckeckFileNameAndGetYear: file must be a string"
        # grab year from file name
        theYear = self.__file.split('IAU')[1].split('.')[0]
        if not self.__isInt(theYear):
            logger.debug("Exiting from __ckeckFileNameAndGetYear with error")
            raise Exception("Can't parse the year from filename: " + file)

        logger.debug("Exiting from __ckeckFileNameAndGetYear with theYear=%s" % theYear)
        return theYear

    def __initGroupAndRefsIAU(self, year):
        """
        Stores the reference to the right publication according to the year.

        :param year: the year
        :type year: str
        """
        logger.debug("Entering in __initGroupAndRefsIAU with year=%s" % year)

        assert isinstance(year, str), "IAUCatalog.__initGroupAndRefsIAU: year must be a string"

        if year == "2000":
            self.__group = "IAU_IAG"
            self.__refsIAU = IAUCatalog.REFERENCES["IAU2000"]
        elif year == "2009":
            self.__group = "IAU"
            self.__refsIAU = IAUCatalog.REFERENCES["IAU2009"]
        elif year == "2015":
            self.__group = "IAU"
            self.__refsIAU = IAUCatalog.REFERENCES["IAU2015"]
        else:
            logger.debug("Exiting from __initGroupAndRefsIAU with error")
            raise Exception("Warning: No reference for the this year: " + year)

        logger.debug("Exiting from __initGroupAndRefsIAU")

    def __isInt(self, string):
        """
        Returns True when the string is an integer otherwise False

        :param string: string to test
        :return: True when the string is an integer otherwise False
        :type string: str
        :rtype: bool
        """

        logger.debug("Entering in __isInt with string=%s" % string)

        try:
            int(string)
            is_int = True
        except:
            is_int = False

        logger.debug("Exiting from __isInt with %s" % is_int)
        return is_int

    def __isNumber(self, a):
        """ Returns True when a is a number otherwise False

        :param a: string to test
        :return: True when a is a number otherwise False
        :type a: str
        :rtype bool
        """

        logger.debug("Entering in __isNumber with a=%s" % a)

        try:
            float(a)
            bool_a = True
        except:
            bool_a = False

        logger.debug("Exiting from __isNumber with %s" % bool_a)
        return bool_a

    def __isEqual(self, number1, number2, allowed_error=1e-9):
        """ Returns True when number1=number2 otherwide False

        :param number1: number to test
        :param number2: number to test
        :param allowed_error: the error for which the numbers are equals
        :return: True when number1=number2 otherwide False
        :type number1: float
        :type number2: float
        :type allowed_error: float
        :rtype: bool
        """

        logger.debug(
            "Entering in __isEqual with number1=%s number2=%s allowed_error=%s" % (number1, number2, allowed_error))

        assert isinstance(number1, (int, float)), "IAUCatalog.__isEqual: %s must be a float or int" % number1
        assert isinstance(number2, (int, float)), "IAUCatalog.__isEqual: %s must be a float or int" % number2
        assert isinstance(allowed_error, (int, float)), "IAUCatalog.__isEqual: %s must be a float or int" % allowed_error
        result = abs(number1 - number2) <= allowed_error

        logger.debug("Exiting from __isEqual with %s" % result)
        return result

    def __isDifferent(self, number1, number2, allowed_error=1e-9):
        """
        Returns True when number1<>number2 otherwise False

        :param number1: number to test
        :param number2: number to test
        :param allowed_error: the error for which the two numbers are equals
        :return: True when number1<>number2 otherwise False
        :type number1: float
        :type number2: float
        :type allowed_error: float
        :rtype: bool
        """
        return not self.__isEqual(number1, number2, allowed_error)

    def __processLine(self, tokens):
        """
        Process a line of the catalog

        :param tokens: the parameters of the catalog
        :return: the crs object
        :type tokens: list
        :rtype: list
        """

        logger.debug("Entering in __processLine with tokens=%s" % tokens)
        crs = []
        theNaifNum = int(tokens[0])
        theTarget = tokens[1]
        theMean = float(tokens[2])
        theA = float(tokens[3])
        theB = float(tokens[4])
        theC = float(tokens[5])
        theRotation = tokens[6] or None
        theLongitudeName = tokens[7] or "Reference_Meridian"
        theLongitudePos = tokens[8] or 0.0
        theLongitudePos = float(theLongitudePos)

        # Check to see if the Mean should be used, for traxial
        # bodies
        # TODO : is it OK ?
        if self.__isDifferent(theA, theB) and self.__isDifferent(theA, theC) and self.__isDifferent(theB, theC) \
                and self.__isDifferent(theMean, -1):
            theA = theMean
            theC = theMean

        flattening = ((theA - theC) / theA)
        if self.__isDifferent(flattening, 0):
            flattening = 1 / flattening

        # create an ocentric CRS
        # From IAU, all CRS can be defined as ocentric with the longitude counted positively to East
        gisCode, ocentric = self.__createOcentricCrs(theNaifNum, theTarget, theA, flattening, theLongitudeName,
                                                     theLongitudePos, theRotation)
        crs.append({
            "authority": "IAU" + str(self.__theYear),
            "code": gisCode,
            "target": theTarget,
            "wkt": ocentric.getWkt(),
            "type": WKT.CRS.OCENTRIC,
            "projection": None
        })

        # create an ographic CRS
        # From IAU, the longitude direction (EAST/WEST) depends on the rotation direction. When the catalog does not have
        # the rotation direction, then the ographic CRS is not created
        # TODO : OK with me ?
        gisCode, ographic = self.__createOgraphicCrs(theNaifNum, theTarget, theA, flattening, theLongitudeName,
                                                     theLongitudePos, theRotation)
        # test if ographic CRS has been created
        if ographic is not None:
            crs.append({
                "authority": "IAU" + str(self.__theYear),
                "code": gisCode,
                "target": theTarget,
                "wkt": ographic.getWkt(),
                "type": WKT.CRS.OGRAPHIC,
                "projection": None
            })
        else:
            logger.warning("No ographic CRS for %s because the rotation direction is not defined." % theTarget)

        # create a projected CRS for each defined Projection on both ocentric and ographic CRS
        projectedCrss = self.__createProjectedCrs(theNaifNum, theTarget, ocentric, ographic)
        crs.extend(projectedCrss)

        logger.debug("Exiting from __processLine with crs=%s" % crs)
        return crs

    def __createOcentricCrs(self, theNaifNum, theTarget, theA, flattening, theLongitudeName, theLongitudePos,
                            theRotation):
        """
        Creates an ocentric CRS based on longitude/latitude

        :param theNaifNum: the Naif Num
        :param theTarget: the target
        :param theA: the radius in meter
        :param flattening: the inverse flattening parameter
        :param theLongitudeName: the longitude name
        :param theLongitudePos: the longitude pos
        :param theRotation: the rotation direction
        :return: a list with the gis code and the ocentric CRS
        :type theNaifNum: int
        :type theTarget: str
        :type theA: float
        :type flattening: float
        :type theLongitudeName: str
        :type theLongitudePos: float
        :type theRotation: str
        :rtype: list
        """

        logger.debug("Entering in __createOcentricCrs with theNaifNum=%s, theTarget=%s, theA=%s, flattening=%s, " \
                     "theLongitudeName=%s, theLongitudePos=%s, theRotation=%s" % (
                         theNaifNum, theTarget, theA, flattening, theLongitudeName, theLongitudePos, theRotation
                     ))

        # define the IAU code
        gisCode = theNaifNum * 100
        ocentric = WKT(theTarget + " " + self.__theYear,
                       "D_" + theTarget + "_" + self.__theYear,
                       theTarget + "_" + self.__theYear + "_" + self.__group,
                       theA,
                       flattening,
                       "IAU" + str(self.__theYear),
                       str(gisCode))

        # set the primem
        if theRotation is None or theRotation.upper() == "DIRECT":
            ocentric.setPrimem(theLongitudeName, theLongitudePos)
        else:
            # invert the longitude when direction is RETROGRADE because we need to transform it in the DIRECT direction
            ocentric.setPrimem(theLongitudeName, theLongitudePos * -1)

        logger.debug("Exiting from __createOcentricCrs with gisCode=%s ographic=%s" % (gisCode, ocentric.getWkt()))
        return [gisCode, ocentric]

    def __createOgraphicCrs(self, theNaifNum, theTarget, theA, flattening, theLongitudeName, theLongitudePos,
                            theRotation):
        """ Creates an ographic CRS based on longitude/latitude
        :param theNaifNum: the Naif Num
        :param theTarget: the target
        :param theA: the radius in meter
        :param flattening: the inverse flattening parameter
        :param theLongitudeName: the longitude name
        :param theLongitudePos: the longitude pos
        :param theRotation: the rotation direction
        :return: a list with the gis code and the ographic CRS
        :type theNaifNum: int
        :type theTarget: str
        :type theA: float
        :type flattening: float
        :type theLongitudeName: str
        :type theLongitudePos: float
        :type theRotation: str
        :rtype: list
        """

        logger.debug("Entering in __createOgraphicCrs with theNaifNum=%s, theTarget=%s, theA=%s, flattening=%s, "
                     "theLongitudeName=%s, theLongitudePos=%s, theRotation=%s" % (
                         theNaifNum, theTarget, theA, flattening, theLongitudeName, theLongitudePos, theRotation
                     ))

        gisCode = theNaifNum * 100 + 1
        ographic = None
        # if not rotation direction, we do not know the direction of axis. So, we do not allow to create an ographic CRS
        if theRotation is not None:
            ographic = WKT(theTarget + " " + self.__theYear,
                           "D_" + theTarget + "_" + self.__theYear,
                           theTarget + "_" + self.__theYear + "_" + self.__group,
                           theA,
                           flattening,
                           "IAU" + str(self.__theYear),
                           str(gisCode))
            ographic.setPrimem(theLongitudeName, theLongitudePos)

            if theTarget.upper() in ["SUN", "EARTH", "MOON"]:
                ographic.setLongitudeAxis(WKT.LongitudeAxis.EAST)
            elif theRotation.upper() == "DIRECT":
                ographic.setLongitudeAxis(WKT.LongitudeAxis.WEST)
            elif theRotation.upper() == "RETROGRADE":
                ographic.setLongitudeAxis(WKT.LongitudeAxis.EAST)
            else:
                raise Exception("The rotation code is unknown : %s" % theRotation)
            logger.debug("Exiting from __createOgraphicCrs with gisCode=%s ographic=%s" % (gisCode, ographic.getWkt()))
        else:
            logger.debug("Exiting from __createOgraphicCrs with gisCode=%s ographic=%s" % (gisCode, ographic))
        return [gisCode, ographic]

    def __createProjectedCrs(self, theNaifNum, theTarget, ocentric, ographic):
        """Creates projected Crs for all defined projection

        :param theNaifNum: the Naif number
        :param theTarget: the target name
        :param ocentric: ocentric CRS
        :param ographic: ographic CRS
        :return: a list that contains all projected CRS
        :type theNaifNum: int
        :type theTarget: str
        :type ocentric: list
        :type ographic: list
        :rtype: a list that contains all projected CRS
        """

        logger.debug("Entering in __createProjectedCrs with theNaifNum=%s, theTarget=%s, ocentric=%s, ographic=%s" % (
            theNaifNum, theTarget, ocentric, ographic
        ))

        crs = []
        # iter on each defined projection
        for projection in WKT.Projection:
            # define ocentric projection
            gisCode = theNaifNum * 100 + projection.value['code']
            prjName = projection.value['projection']
            ocentric.setProjection(theTarget + "_" + prjName, projection, "IAU" + self.__theYear, str(gisCode))
            # save projection
            crs.append({
                "authority": "IAU" + str(self.__theYear),
                "code": gisCode,
                "target": theTarget,
                "wkt": ocentric.getWkt(),
                "type": WKT.CRS.PROJECTED_OCENTRIC,
                "projection":projection
            })
            # unset projection
            ocentric.unsetProjection()

            # define ographic projection when ographic CRS is defined
            if ographic is not None:
                gisCode = gisCode + 1
                ographic.setProjection(theTarget + "_" + prjName, projection, "IAU" + self.__theYear, str(gisCode))
                # save projection
                crs.append({
                    "authority": "IAU" + str(self.__theYear),
                    "code": gisCode,
                    "target": theTarget,
                    "wkt": ographic.getWkt(),
                    "type": WKT.CRS.PROJECTED_OGRAPHIC,
                    "projection": projection
                })

                # unset projection
                ographic.unsetProjection()

        logger.debug("Exiting from __createProjectedCrs with %s" % crs)
        return crs

    def getRefsIAU(self):
        """
        Returns ref IAU
        :return:  the ref IAU
        :rtype: str
        """
        return self.__refsIAU

    def processFile(self):
        """
        Process the catalog

        :return: A list that contains all CRS
        :rtype: float
        """

        logger.debug("Entering in processFile")

        data = []
        for line in open(self.__file):
            tokens = line.rstrip().split(',')
            if not self.__isInt(tokens[0]) or (self.__isEqual(float(tokens[2]), -1)
                                               and self.__isEqual(float(tokens[3]), -1)
                                               and self.__isEqual(float(tokens[4]), -1)):
                logger.warning("%s is ignored", tokens)
            else:
                # Then Radii values exist in input table and naif is a number
                data.extend(self.__processLine(tokens))

        logger.debug("Exiting from processFile with %s CRS" % len(data))
        return data

    @staticmethod
    def saveAsProj4(crss, filename=None):
        """
        Save the crs list as initFile in proj4
        :param crss: crs list
        :param filename: output filename
        """

        logger.warning("Export only ocentric CRS or projected ocentric CRS while proj4 does not convert correctly "
                       "ocentric latitude to ographic latitude")
        hasValidationError = False
        if filename is None:
            filename = crss[0]['authority']

        if filename and filename is not sys.stdout:
            fileToOutput = open(filename, 'w')
        else:
            fileToOutput = filename

        try:
            fileToOutput.write("%s\n" % IAUCatalog.REFERENCES[crss[0]['authority']])
            for crs in crss:
                crsType = crs['type']
                # use only ocentric or projected ocentric while proj4 cannot convert ocentric latitude to ographic latitude
                # in the right way. Actually, there is an error (~20m on Earth at latitude 45)
                # TODO : Ok with me ?
                if crsType == WKT.CRS.OCENTRIC or crsType == WKT.CRS.PROJECTED_OCENTRIC:
                    result, projString, wkt = WKT.isValid(crs['wkt'])
                    if result:
                        if crs['projection'] is None:
                            projection = ""
                        else:
                            projection = " - "+crs['projection'].value['projection']

                        fileToOutput.write(
                            "#%s : %s WKT Codes for %s : %s %s\n" % (
                                crs['code'], crs['authority'], crs['target'], crs['type'].value, projection
                            )
                        )
                        fileToOutput.write("<%s> %s\n" % (crs['code'], projString))
                    else:
                        hasValidationError = True
            fileToOutput.close()

            if hasValidationError:
                raise WKT.ValidationError()

        finally:
            if fileToOutput is not sys.stdout:
                fileToOutput.close()

    @staticmethod
    def saveAsWKT(crss, filename=None):
        """ Save the list of CRS in a file

        :param crss: the list that contains all CRS
        :param filename: output filename
        """
        hasValidationError = False
        if filename is None:
            filename = crss[0]['authority'] + "_v4.wkt"

        if filename and filename is not sys.stdout:
            fileToOutput = open(filename, 'w')
        else:
            fileToOutput = filename

        try:
            target = ""
            authority = crss[0]['authority']
            fileToOutput.write("%s\n" % IAUCatalog.REFERENCES[authority])
            for crs in crss:
                if crs['target'] != target:  # authority
                    fileToOutput.write("\n\n#%s WKT Codes for %s\n" % (crs['authority'], crs['target']))
                    target = crs['target']
                result, projString, wkt = WKT.isValid(crs['wkt'])
                if result:
                    fileToOutput.write("%s,%s\n" % (crs['code'], wkt))
                else:
                    hasValidationError = True
                    fileToOutput.write("# %s,%s\n" % (crs['code'], wkt))

            if hasValidationError:
                raise WKT.ValidationError()
        finally:
            if fileToOutput is not sys.stdout:
                fileToOutput.close()

    @staticmethod
    def saveAsPrj(crss):
        logger.warning("Export only ocentric CRS while proj4 does not convert correctly "
                       "ocentric latitude to ographic latitude")
        hasValidationError = False
        for crs in crss:
            # TODO : I only export Ocentric while the ographic problem is not solved with proj4. OK with me ?
            if crs['type'] == WKT.CRS.PROJECTED_OCENTRIC:
                year = crs['authority'].replace("IAU", "")
                wkt = crs['wkt']
                target = crs['target']
                result, projString, wkt = WKT.isValid(wkt)
                if result:
                    outputPrjFile = "%s %s.prj" % (target, year)
                    fileToOutput = open(outputPrjFile, 'w')
                    fileToOutput.write("%s" % wkt)
                    fileToOutput.close()
                else:
                    hasValidationError = True
                    logger.error("WKT %s is not valid" % wkt)

        if hasValidationError:
            raise WKT.ValidationError()

    @staticmethod
    def saveAs(crss, filename=None, format="WKT"):
        """ Save the list of CRS in a file

        :param crss: the list that contains all CRS
        :param filename:
        :param format: Output format. It can be WKT, PROJ or PRJ (default WKT)
        """
        if format == "WKT":
            IAUCatalog.saveAsWKT(crss, filename)
        elif format == "PROJ":
            IAUCatalog.saveAsProj4(crss, filename)
        elif format == "PRJ":
            logger.warning("output filename is ignored for PRJ format")
            IAUCatalog.saveAsPrj(crss)
        else:
            raise Exception("Unknown output format")


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


def initLogger(logger, LEVEL_LOG):
    """
    Init the logger.

    The info level format of the logger is set to "%(asctime)s :: %(levelname)s :: %(message)s"  and the debug
    level format is set to "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s". The logs output is set
    to the console

    :param logger: logger
    :param LEVEL_LOG: logger level
    """

    FORMAT_INFO = "%(asctime)s :: %(levelname)s :: %(message)s"
    FORMAT_DEBUG = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    # fh = logging.FileHandler('get_iau2000.log')
    logging.StreamHandler()
    if LEVEL_LOG == logging.INFO:
        logging.basicConfig(format=FORMAT_INFO)
    else:
        logging.basicConfig(format=FORMAT_DEBUG)
    # logger.addHandler(fh)
    logger.setLevel(LEVEL_LOG)
    try:
        coloredlogs.install()
    except:
        pass


def timeSpend(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        result = func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        logger.info("function [{}] finished in {} ms".format(
            func.__name__, int(elapsedTime * 1000)
        ))
        return result

    return newfunc


@timeSpend
def loadAndProcessCatalog(data):
    """
    Load and process the IAU CSV file
    :param data: IAU CSV file
    :return: the list of WKT
    """
    iauData = IAUCatalog(data)
    return iauData.processFile()


@timeSpend
def saveAs(wktList, outputFile, format):
    IAUCatalog.saveAs(wktList, outputFile, format=format)


def main(argv):
    parser = argparse.ArgumentParser(description="Converts IAU CSV file into WKT/proj4/prj format, for example: "
                                                 "python %s naifcodes_radii_m_wAsteroids_IAU2015.csv\n" % (
                                                     os.path.basename(sys.argv[0])
                                                 ),
                                     formatter_class=SmartFormatter,
                                     epilog="Authors: Trent Hare (USGS), Jean-Christophe Malapert (CNES)"
                                            " - License : Public Domain ",
                                     )
    parser.add_argument('csv', metavar='csv_file', nargs=1, help='data from IAU as CSV file')
    parser.add_argument('--output', metavar='output', nargs=1, help="output file (default is stdout)")
    parser.add_argument('--format', choices=['WKT', 'PROJ', 'PRJ'], help="output format (default is WKT)")
    parser.add_argument('--verbose', choices=['OFF', 'INFO', 'DEBUG'],
                        help="R|select the verbose mode on stdout (INFO is default) where:\n"
                             " OFF : do not display error,\n"
                             " INFO : display error,\n"
                             " DEBUG: display each input/output of each method\n")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s V1.0 (28/08/2018)',
                        help="show program's version number and exit.")
    args = parser.parse_args()

    # handling positional argument
    data = None
    if args.csv:
        data = args.csv[0]
        if not os.path.isfile(data):
            parser.error("File not found")

    # handling outputFile argument
    if args.output:
        outputFile = args.output[0]
    else:
        outputFile = sys.stdout

    # handling format argument
    if args.format:
        format = args.format
    else:
        format = "WKT"

    # handling verbose argument
    if args.verbose:
        if args.verbose != "OFF":
            verbose = logging.getLevelName(args.verbose)
            logger.setLevel(verbose)
        else:
            verbose = "OFF"
    else:
        verbose = logging.INFO
        logger.setLevel(verbose)

    if verbose == "OFF":
        logger.disabled = True
    else:
        logger.disabled = False

    try:
        wktList = loadAndProcessCatalog(data)
        logger.info("%s WKTs loaded from %s" % (len(wktList), data))
        saveAs(wktList, outputFile, format)
    except WKT.ValidationError:
        logger.error("Error durring the WKT validation")
        sys.exit(1)
    except Exception as message:
        logger.error("Error: %s" % message)
        sys.exit(2)


if __name__ == "__main__":
    LEVEL_LOG = logging.INFO
    logger = logging.getLogger()
    logger.disabled = False
    initLogger(logger, LEVEL_LOG)

    sys.exit(main(sys.argv))
