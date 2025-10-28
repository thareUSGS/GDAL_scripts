convert_xyzi2vrt.py

Purpose: Create a *.csv and GDAL *.vrt for LOLA xyzi binary formatted files produced by Goddard.
XYZI files are Lunar based X,Y,Z,date lidar shot points from the LOLA instrument. Example files
can be found at https://pgda.gsfc.nasa.gov/products/78. GDAL VRT files can be used within GDAL
tools (e.g., ogrinfo or ogr2ogr) or directly in applications like QGIS.

Author:  Trent Hare, <trent.m.hare@gmail.com>
Date:    Oct 27, 2025
version: 0.1

Created with tips from CoPilot AI.

Usage: `python convert_xyzi2vrt.py Site01_final_adj.xyzi` 
*  output will be a Site01_final_adj.csv and Site01_final_adj.vrt files

Environment:
installed miniforge, with gdal (conda install gdal).

Note gdal is not needed to run this script, but it is good to test the vrt using gdal tools. 
for example:
`gdalinfo in.vrt`

---

From Goddard Readme (https://pgda.gsfc.nasa.gov/products/78):

*.xyzi - final point clouds after track adjustments and cleaning
Data format: Binary double precision floating point tables with 4 columns: X, Y, Z, RDRid
where X,Y,Z are the polar stereographic coordinates (in km) and RDRid is the LOLA RDR ID for each point with the format: YYDOYHHMM

The site name numbering follows the paper:
Illumination conditions of the lunar polar regions using LOLA topography
Mazarico, E., et al. Icarus, Volume 211, Issue 2, February 2011, Pages 1066-1081
https://doi.org/10.1016/j.icarus.2010.10.030

Please refer to the following paper for further details.
Barker et al., 2021, "Improved LOLA Elevation Maps for South Pole Landing Sites: Error Estimates and Their Impact on Illumination Conditions", Planetary & Space Science, Volume 203, 1 September 2021, 105119, https://doi.org/10.1016/j.pss.2020.105119