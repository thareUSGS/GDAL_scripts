# script recusrively searches for downloaded STAC items (*.json),
# grabs the geometry and appends to a single shapefile.
# license: CC0, public domain
# help from AI, Trent Hare

import os, sys
import json
import pystac
from osgeo import ogr, osr

# Function to process a single STAC JSON file
def process_stac_file(file_path, layer):
    with open(file_path) as f:
        # Create a PySTAC Item from the dictionary
        stac_items = json.load(f)
        item = pystac.Item.from_dict(stac_items)
        geom = repr(item.geometry)
        #print(repr(geom))
           
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(ogr.CreateGeometryFromJson(geom))
        feature.SetField("id", item.id)
        layer.CreateFeature(feature)
        feature = None

def main():
    if len(sys.argv) < 2:
        print("Usage: python " + sys.argv[0] + " <filename>")
        sys.exit(1)
    outfilename = sys.argv[1]

    # Create a shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(outfilename)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = data_source.CreateLayer("layer", srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("id", ogr.OFTString))

    # Recursively find all JSON files in the current directory
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                process_stac_file(file_path, layer)
                print("loaded geom from: " + file_path)

    # Close the data source
    data_source = None

if __name__ == "__main__":
    main()
    print("completed. This has not converted a 0-360 range to a -180 to 180")
    print("to do that: ogr2ogr -f 'ESRI Shapefile' output180.shp input360.shp -wrapdateline")
