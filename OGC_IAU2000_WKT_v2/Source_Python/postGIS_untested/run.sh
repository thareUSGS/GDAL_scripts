#!/bin/bash
python create_PostGIS_IAU2000_wkt_proj4_INSERT.py ../../naifcodes_radii_m_wAsteroids_IAU2000.csv insert_PostGIS_SRID_IAU2000.txt
python create_PostGIS_IAU2000_wkt_proj4_INSERT.py ../../naifcodes_radii_m_wAsteroids_IAU2009.csv insert_PostGIS_SRID_IAU2009.txt
