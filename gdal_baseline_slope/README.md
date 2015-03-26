
Purpose:  Given a DEM, calculate specialized slopes using various baseline
           lengths (1 baseline, 2 baseline, 5 baseline). Also a more normal (3x3 Horn method)
           slope equation is available which is used if no baseline parameter is sent.

Install: Recommended environment is Anacoda Python. To get GDAL added to Anacoda run "conda install gdal". Requires GDAL, Numpy, and SciPy.

Usage: python gdal_baseline_slope.py [-baseline 1,2,5] [-ot Byte] [-crop] infile outfile.tif
       
       where [] indicates optional parameters
       warning: current implmentation loads full image into memory and is fairly slow. 
     
       -ot Byte will scale 32bit floating point values to 8bit using; DN = (Slope * 5) + 0.2  
       -crop: will trim image 1 to 5 pixels from image edge based on selected baseline amount.
       
       Future: Speed up implementation if possible.
