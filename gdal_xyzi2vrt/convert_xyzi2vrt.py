# convert_xyzi2vrt.py
#
# Purpose: Create a *.csv and GDAL *.vrt for LOLA xyzi binary formatted files produced by Goddard.
# XYZI files are Lunar based X,Y,Z,date lidar shot points from the LOLA instrument. Example files
# can be found at https://pgda.gsfc.nasa.gov/products/78
# 
# Author:  Trent Hare, <trent.m.hare@gmail.com>
# Date:    Oct 27, 2025
# version: 0.1
# License: CC0 (public domain)

import struct
import csv
import os
import sys

def convert_binary_to_csv_and_vrt(input_file):
    # Derive output filenames
    base_name = os.path.splitext(input_file)[0]
    csv_file = f"{base_name}.csv"
    vrt_file = f"{base_name}.vrt"

    record_size = 4 * 8  # 32 bytes for 4 float64 values

    with open(input_file, 'rb') as bin_file, open(csv_file, 'w', newline='') as out_csv:
        writer = csv.writer(out_csv)
        writer.writerow(['X_m', 'Y_m', 'Z_m', 'RDRid_YYDOYHHMM'])

        while True:
            bytes_read = bin_file.read(record_size)
            if not bytes_read or len(bytes_read) < record_size:
                break

            x_km, y_km, z_km, rdrid = struct.unpack('<dddd', bytes_read)
            rdrid_str = f"{int(round(rdrid)):09d}"
            writer.writerow([x_km * 1000, y_km * 1000, z_km * 1000, rdrid_str])

    vrt_content = f"""<OGRVRTDataSource>
  <OGRVRTLayer name="{base_name}">
    <SrcDataSource relativeToVRT="1">{csv_file}</SrcDataSource>
    <LayerSRS>IAU_2015:30135</LayerSRS>
    <GeometryType>wkbPoint25D</GeometryType>
    <GeometryField encoding="PointFromColumns" x="X_m" y="Y_m" z="Z_m"/>
    <Field name="X_m" type="Real" />
    <Field name="Y_m" type="Real" />
    <Field name="Z_m" type="Real" />
    <Field name="RDRid_YYDOYHHMM" type="String" />
  </OGRVRTLayer>
</OGRVRTDataSource>
"""

    with open(vrt_file, 'w') as f:
        f.write(vrt_content)

    print(f" CSV written to: {csv_file}")
    print(f" VRT written to: {vrt_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_xyzi2vrt.py <input_binary_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    convert_binary_to_csv_and_vrt(input_file)
