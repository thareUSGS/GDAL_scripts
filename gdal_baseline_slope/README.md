
Purpose:  Given a DEM, calculate specialized slopes using various baseline
           lengths (1 baseline, 2 baseline, 5 baseline). Also a more normal
           slope equation is available which is used if no baseline parameter is sent.

Install: Recommended environment is Anacoda Python. To get GDAL added to Anacoda run "conda install gdal". Requires GDAL, Numpy, and SciPy.

Usage: python gdal_baseline_slope.py [-baseline 1,2,5] [-ot Byte] infile outfile.tif
       
       where [] indicates optional parameters
       warning: current implmentation loads full image into memory and is fairly slow. 
       
       Future: optionally trim image to clean edges. Currently they are appropriately set to NoDATA. Spped up implementation if possible.
