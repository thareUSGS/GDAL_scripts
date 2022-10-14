import os, sys
from osgeo import gdal

def match_extent ( primary, replica ):
    """This function forces an image (``replica``) to
    match the extent and projection of another
    (``primary``) using GDAL. The output resolution is
    automated in the gdal_translate run. The newly created image
    is a GDAL GTIFF file.

    Parameters
    -------------
    primary: str 
        A filename (with full path if required) with the 
        primary image (that that will be taken as a reference
        and matched)
    replica: str 
        A filename (with path if needed) with the image
        that will be modified
    Returns
    ----------
    The output filename
    """

    primary_ds = gdal.Open( primary )
    if (primary_ds is None):
        raise (IOError, "GDAL could not open primary file %s " \
            % primary)
    primary_proj = primary_ds.GetProjection()
    primary_geotrans = primary_ds.GetGeoTransform()
    w = primary_ds.RasterXSize
    h = primary_ds.RasterYSize

    ulx, uly = gdal.ApplyGeoTransform(primary_geotrans,0,0)    # print('Upper Left Corner:',
    #urx, ury = gdal.ApplyGeoTransform(primary_ds,w,0)         # print('Upper Right Corner:', 
    #llx, lly = gdal.ApplyGeoTransform(primary_ds,0,h)         # print('Lower Left Corner:', 
    lrx, lry = gdal.ApplyGeoTransform(primary_geotrans,w,h)    # print('Lower Right Corner:', 

    root, ext = os.path.splitext(replica)
    dst_filename = root + "_match.tif"
    cmd = "gdal_translate -a_ullr {} {} {} {} -a_srs {} {} {}".format(ulx, uly, lrx, lry, primary_proj, replica, dst_filename)
    os.system(cmd)

    return (dst_filename)

# =============================================================================
# 	Main
if (len(sys.argv) < 2):
  print("need input and output files")
  sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

outname = match_extent(infile, outfile)
print("{} created".format(outname))

