from osgeo import gdal
import sys, os, time
import subprocess

# Define source raster and output parameters
input_raster = sys.argv[1] 
output_raster = sys.argv[2]
min_lat = -90  # Adjust as needed
max_lat = 90
latband_size = 5  # Degrees

# Extract latitude bands in 5 degrees, with local standard parallel, following HIRISE scheme
for lat in range(min_lat, max_lat, latband_size):
    min_band_lat = lat
    max_band_lat = lat + latband_size
    if (max_band_lat > 0):
       stand_par = min_band_lat
    else:
       stand_par = max_band_lat

    output_tile = output_raster + "_n" + str(int(max_band_lat)) + "s" + str(int(min_band_lat)) + "_standpar" + str(int(stand_par)) + ".tif"
    print("writing: " + output_tile)

    # Use gdal.Warp to crop, apply projection, and set output resolution
    gdal.Warp(
        output_tile,
        input_raster,
        dstSRS=f"+proj=eqc +lat_ts={stand_par} +R=1737400",  # Equirectangular projection with dynamic standard parallel
        outputBounds=[-180, min_band_lat, 180, max_band_lat],  # Geographic bounds (longitude, latitude)
        outputBoundsSRS="IAU_2015:30100",  # Geographic coordinate system
        xRes=100,  # Set horizontal resolution
        yRes=100   # Set vertical resolution
    )


    # Execute the Python command
    # NewStandardPar_Equi.py [-of format] [-clat newClat] infile outfile
    output_vrt = output_raster + "_n" + str(int(max_band_lat)) + "s" + str(int(min_band_lat)) + "_standpar" + str(int(stand_par)) + "_global0.vrt"
    vrt0 = f"python NewStandardPar_Equi.py -of VRT -clat 0 {output_tile} {output_vrt}"
    subprocess.call(vrt0, shell=True)

print("Extraction complete!")
