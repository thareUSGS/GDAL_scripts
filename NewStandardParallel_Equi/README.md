NewStandardParallel_Equi.py

Purpose: Set new standard_parallel_1 without reprojecting the image,
         just changes registration and X cellsize. This should only be used for
         projections like Equirectangular. This can result in rectangular pixels.
 
 Author: Trent Hare (USGS), Apr 2023
 
 Based on tolatlong by Andrey Kiselev, dron@remotesensing.org

Usage: NewCenterLon_Equi.py [-of format] [-clat newClat] infile outfile

