import sys
from osgeo import gdal

def Usage():
   print('usage:\n')
   print(argv[0] + ' in.file  output.tif min_valid max_valid [output_noData]')
   print(argv[0] + ' input.tif output.tif 0 1')
   print('\n  --only set output_noData, if the original file has none set.')
   sys.exit(1)
    
argv = gdal.GeneralCmdLineProcessor( sys.argv )
if argv is None:
    sys.exit(0)

if (len(argv) != 5 and len(argv) != 6):
    Usage()
    
infile = sys.argv[1]
outfile = sys.argv[2]
minValue = float(sys.argv[3])
maxValue = float(sys.argv[4])
noData = None
print ("input file: " + infile)
print ("min: " + str(minValue))
print ("max: " + str(maxValue))
if (len(argv) == 6):
   noData = float(sys.argv[5])

# open dataset and loop over bands to get a numpy array
ds = gdal.Open(infile)
# open output dataset, which is a copy of original
driver = gdal.GetDriverByName('GTiff')
dsOut = driver.CreateCopy(outfile, ds)

for i in range(ds.RasterCount):
   band = ds.GetRasterBand(i + 1)
   data = band.ReadAsArray()
   if (noData == None):
      noData = band.GetNoDataValue()
   print ("NoData: " + str(noData))

   # modify numpy array to defined range
   data[(data < minValue) | (data > maxValue)] = noData

   # write the modified array to the raster
   bandOut = dsOut.GetRasterBand(i + 1)
   bandOut.WriteArray(data)
   bandOut.SetNoDataValue(noData)

   #seems odd, but must clear out original stats for each band
   for key in bandOut.GetMetadata().keys():
         if key.startswith("STATISTICS_"):
            bandOut.SetMetadataItem(key, None)
        
dsOut.FlushCache()
print("file created: " + outfile)