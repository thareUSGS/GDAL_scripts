import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon


def safe_float(x):
    try:
        return float(x)
    except ValueError:
        return float('nan')

def ascii_to_gis(input_file, output_file, crs_code="IAU_2015:30100"):
    # Load ASCII file, skipping lines that start with '#'

    df = pd.read_csv(
        input_file,
        sep=r"[,\s]+",  # Split on commas OR whitespace
        comment="#",
        header=None,
        names=["Lat_min", "Lat_max", "Lon_min", "Lon_max", "H_ppm"],
        #dtype={"Lat_min": float, "Lat_max": float, "Lon_min": float, "Lon_max": float, "H_ppm": float},
        converters={
            "Lat_min": safe_float,
            "Lat_max": safe_float,
            "Lon_min": safe_float,
            "Lon_max": safe_float,
            "H_ppm": safe_float
        },
        engine="python"
    ).dropna()

    # Create polygons
    polygons = []
    for _, row in df.iterrows():
        coords = [
            (row["Lon_min"], row["Lat_min"]),
            (row["Lon_max"], row["Lat_min"]),
            (row["Lon_max"], row["Lat_max"]),
            (row["Lon_min"], row["Lat_max"])
        ]
        polygons.append(Polygon(coords))

    # Create GeoDataFrame with user-specified CRS
    gdf = gpd.GeoDataFrame(df, geometry=polygons, crs=crs_code)

    # Save to Shapefile or GeoJSON
    if output_file.lower().endswith(".shp"):
        gdf.to_file(output_file)
        print(f"Shapefile saved to {output_file} with CRS {crs_code}")
    elif output_file.lower().endswith(".geojson"):
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"GeoJSON saved to {output_file} with CRS {crs_code}")
    else:
        print("Error: Output file must end with .shp or .geojson")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python ascii_to_gis.py <input_ascii_file> <output_file.shp|output_file.geojson> [CRS]")
        print("Example: python ascii_to_gis.py hydrogenhd.txt hydrogen_polygons.geojson IAU_2015:30100")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    crs_code = sys.argv[3] if len(sys.argv) == 4 else "IAU_2015:30100"
    ascii_to_gis(input_file, output_file, crs_code)


