gdal_clip2range
============
description: This routine was written to clip pixel values to a defined range. All values outside that range will be set to a single NoData value. If there is a NoDATA value in the input file, it is best to *not* set the optional "output_noData". If there is not a NoData value set in the input file, then you can set the output NoData value.

#### Usage:
`gdal_clip2range.py in.file  output.tif min_valid max_valid [output_noData]`

`gdal_clip2range.py input.tif output.tif -100.5 500.2`
This example will set pixel values less than -100.5 and greater than 500.2 to NoDATA. It will maintain the original NoDATA value to the output file.

or

_reminder_: only set the optional output_noData, if the original file has none set. For example:

`python gdal_clip2range.py input.tif output.tif 0 1 0`

This example will clip any pixels outside the range of 0 to 1 to NoDATA. It will also define the NoDATA in the output file to 0. This example might be used to set a valid range for I/F 32bit floating point image.

more: https://openplanetary.discourse.group/t/crop-image-dn-range-gdal-clip2range-py/698
