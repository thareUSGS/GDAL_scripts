gdal_copylabel.py

Description: Copies label's projection from one image to another (allows new pixel offset also)

Usage: gdal_copylabel.py [-of format] [-shiftX pixels] [-shiftY pixels (neg)] infile copyfile outfile

Example:
 
 % gdal_copylabel.py -of vrt -shiftX 0.5 -shiftY -0.5 adir_DEM_1m_InSightE08_E_isis2_02_02_ang.cub DEM_1m_InSightE08_E_isis3.cub adir_DEM_1m_InSightE08_E_isis2_02_02_ang.vrt
 
   note: A GDAL VRT is a virtual format which simply points to the original "infile" for the pixels (data). To burn this label into a new image use gdal_translate.
 
   % gdal_translate  adir_DEM_1m_InSightE08_E_isis2_02_02_ang.vrt adir_DEM_1m_InSightE08_E_isis2_02_02_ang.tif
 
