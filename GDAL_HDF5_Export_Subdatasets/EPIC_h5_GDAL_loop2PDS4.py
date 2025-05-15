from osgeo import gdal
import sys

# Open the HDF5 file
hdf5_file = sys.argv[1]
dataset = gdal.Open(hdf5_file, gdal.GA_ReadOnly)

# Get subdatasets (each represents a different layer)
subdatasets = dataset.GetSubDatasets()

# Loop through each subdataset and export
cnt = 0
for i, (subdataset_name, subdataset_desc) in enumerate(subdatasets):
    #print(f"Processing subdataset {i}: {subdataset_name}")

    # Open subdataset
    subdataset = gdal.Open(subdataset_name, gdal.GA_ReadOnly)
    
    if subdataset:

        subdataset_clean = subdataset_name.replace('"','')

        if ("Image" in subdataset_desc):
            str_array = subdataset_desc.split("/")
            nm = str_array[2].replace("Band","")
            output_prefix = sys.argv[1].replace(".h5","")
            #output_XML = output_prefix + f"_{nm}" + ".xml"
            output_XML = output_prefix + f"_{nm}_image" + ".xml"
            #output_IMG = output_prefix + f"_{nm}_image" + ".img"
            #createOptions = ["IMAGE_FILENAME="+output_IMG, "ARRAY_IDENTIFIER="+subdataset_clean]

            createOptions = ["ARRAY_IDENTIFIER="+subdataset_clean]
            gdal.Translate(output_XML, subdataset, format="PDS4", creationOptions=createOptions)
            cnt = cnt + 1

        if ("PixelType" in subdataset_desc):
            output_XML = output_prefix + f"_{nm}_pixeltype" + ".xml"
            #GDAL can't append to a new image/raw pixel file
            #output_PT = output_prefix + f"_{nm}_pixeltype" + ".img"
            #createOptions = ["IMAGE_FILENAME="+output_IMG,"APPEND_SUBDATASET=YES","ARRAY_IDENTIFIER="+subdataset_clean]

            createOptions = ["ARRAY_IDENTIFIER="+subdataset_clean]
            gdal.Translate(output_XML, subdataset, format="PDS4", creationOptions=createOptions)

        subdataset = None  # Close subdataset

dataset = None  # Close main dataset
print('{output_PDS4} : ' + str(cnt) + ' layers/subdatasets exported successfully.')

