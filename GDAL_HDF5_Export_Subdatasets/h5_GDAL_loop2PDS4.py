from osgeo import gdal
import sys

# Open the HDF5 file
hdf5_file = sys.argv[1]
output_PDS4 = sys.argv[2]

dataset = gdal.Open(hdf5_file, gdal.GA_ReadOnly)

# Get subdatasets (each represents a different layer)
subdatasets = dataset.GetSubDatasets()

# Loop through each subdataset and export
for i, (subdataset_name, subdataset_desc) in enumerate(subdatasets):
    print(f"Processing subdataset {i}: {subdataset_name}")

    # Open subdataset
    subdataset = gdal.Open(subdataset_name, gdal.GA_ReadOnly)
    
    if subdataset:

        subdataset_clean = subdataset_name.replace('"','')
        if (i==0): #first layer create not append
             createOptions = ["ARRAY_IDENTIFIER="+subdataset_clean]
        else: 
             createOptions = ["APPEND_SUBDATASET=YES","ARRAY_IDENTIFIER="+subdataset_clean]

        gdal.Translate(output_PDS4, subdataset, format="PDS4", creationOptions=createOptions)

        subdataset = None  # Close subdataset

dataset = None  # Close main dataset

print('{output_PDS4} : ' + str(i) + ' layers/subdatasets exported successfully.')


