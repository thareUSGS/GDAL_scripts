
Purpose:  Given a DEM, calculate specialized slopes using various baseline
           lengths (1 baseline, 2 baseline, 5 baseline). Also a more normal (3x3 Horn method)
           slope equation is available which is used if no baseline parameter is sent.

updates:
         T. Hare - August 2017. Upgraded to Python3.x

Install: Recommended environment is Anacoda Python. To get GDAL added to Anacoda run "conda install gdal". Requires GDAL, Numpy, and SciPy.

Usage: python gdal_baseline_slope.py [-baseline 1,2,5] [-ot Byte] [-crop] infile outfile.tif
       
       where [] indicates optional parameters
       warning: current implmentation loads full image into memory and is fairly slow. 
     
       -ot Byte will scale 32bit floating point values to 8bit using; DN = (Slope * 5) + 0.2 
                 although we will still generated 32bit versions (as requested by team).
       -crop: will trim image 1 to 5 pixels from image edge based on selected baseline amount.
       
       Future: Speed up implementation if possible.


Examples for how an a-direction baseline slope is calculated:

For a baseline = 2:
 
        #Uses a moving 3x3 pixel window, but only the 4 corners are used in the calculation
        #ignoring all the internal "z" pixels
        [a, z, b,
         z, z, z,
         c, z, d] = in_filter

        dz_dx = ((b + d) - (a + c)) / (baseline * float(x_cellsize))
        dz_dy = ((a + b) - (c + d)) / (baseline * float(y_cellsize))
        slope = np.sqrt(dz_dx**2 + dz_dy**2)
        return np.degrees(np.arctan(slope)) #return slope in degrees rather than radians

For a baseline = 5:

        #Uses a moving 6x6 pixel window, but again only the 4 corners are used in the calculation
        #ignoring all the internal "z" pixels
        [ a,  z,  z,  z,  z,  b, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          z,  z,  z,  z,  z,  z, 
          c,  z,  z,  z,  z,  d] = in_filter

          same equation used above, where baseline variable = 5 here.

for more see on sptial filters: https://doi-usgs.github.io/ISIS3/The_Power_of_Spatial_Filters.html
