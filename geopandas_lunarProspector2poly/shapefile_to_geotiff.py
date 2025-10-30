import sys
from osgeo import gdal, ogr

def shapefile_to_geotiff(shapefile, output_tiff, pixel_size=0.5, attribute="H_ppm"):
    """
    Convert a shapefile to a GeoTIFF raster using GDAL.
    - shapefile: input shapefile path
    - output_tiff: output GeoTIFF path
    - pixel_size: resolution in degrees (default 0.5 for half-degree grid)
    - attribute: field name to rasterize (default 'H_ppm')
    """

    # Open shapefile
    source_ds = ogr.Open(shapefile)
    if source_ds is None:
        raise RuntimeError(f"Cannot open shapefile: {shapefile}")
    source_layer = source_ds.GetLayer()

    # Get CRS from shapefile
    source_srs = source_layer.GetSpatialRef()
    if source_srs is None:
        raise RuntimeError("Shapefile has no CRS defined.")

    # Define raster bounds (-180 to 180, -90 to 90)
    x_min, x_max, y_min, y_max = -180.0, 180.0, -90.0, 90.0

    # Calculate raster size
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)


    # Create GeoTIFF with LZW compression
    options = ["COMPRESS=LZW", "TILED=YES"]
    target_ds = gdal.GetDriverByName('GTiff').Create(output_tiff, x_res, y_res, 1, gdal.GDT_Float32, options)
    target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    target_ds.SetProjection(source_srs.ExportToWkt())

    # Set NoData value
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(-32768)

    # Rasterize using attribute field
    gdal.RasterizeLayer(target_ds, [1], source_layer, options=[f"ATTRIBUTE={attribute}"])

    # Close datasets
    target_ds = None
    source_ds = None
    print(f" GeoTIFF saved to {output_tiff} with CRS from shapefile and bounds {x_min},{x_max},{y_min},{y_max}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python shapefile_to_geotiff.py <input_shapefile.shp> <output.tif> [pixel_size]")
        print("Example: python shapefile_to_geotiff.py hydrogen_polygons.shp hydrogen_raster.tif 0.5")
        sys.exit(1)

    shapefile = sys.argv[1]
    output_tiff = sys.argv[2]
    pixel_size = float(sys.argv[3]) if len(sys.argv) == 4 else 0.5
    shapefile_to_geotiff(shapefile, output_tiff, pixel_size)