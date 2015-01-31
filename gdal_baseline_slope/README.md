
Purpose:  Given a DEM, calculate specialized slopes using various baseline
           lengths (1 baseline, 2 baseline, 5 baseline). Also a more normal
           slope equation is available which is used if no baseline parameter is sent.

Usage: gdal_baseline_slope.py [-baseline 1,2,5] [-ot Byte] infile outfile.tif
       where [] indicates optional parameters
