gdal2PLY.py

Create a 3D binary PLY format from a DEM/DTM

usage:
python gdal2PLY.py in.tif out.ply


History
# script originally posted to gis-stackexchange by Jake
# http://gis.stackexchange.com/questions/121561/generating-a-mesh-from-dtm
# Jake: http://gis.stackexchange.com/users/1931/jake
# original name: gdal_ratertotrn.py
# date posted on stackexchange: Nov 12 2014
#

 NoData work-around using GDAL
 1.) find minimum Z value
 > gdalinfo -mm in_DEM.tif
 let's say min = -2790.594

2.) map GDAL Nodata to next round value down = -2791.
   -- if DEM is large resample also. Example below resamples to 10 m/p
 > gdalwarp -dstnodata -2791 -tr 10 10 -r bilinear in_DEM.tif in_DEM_10m_nodata.tif

3.) now run this program in Python. I recommend Anaconda. Once installed type "conda instal gdal".
 > python gdal2PLY.py in_DEM_10m_nodata.tif out_DEM_10m.ply
