gdal_clip2range
============
description: This routine was written to clip pixel values to a defined range. All values outside that reange will be set to a single NoData value. If there is a NoDATA value in the input file, it is best to *not* set the optional "output_noData". If there is not a NoData value set in the input file, then you can set the output NoData value.

#### Usage:
`gdal_clip2range.py in.file  output.tif min_valid max_valid [output_noData]`

`gdal_clip2range.py input.tif output.tif -100.5 500.2`
This example will clip the pixel DN range to less than -100.5 and greater than 500.2. It will maintain the original NoDATA value.

or

only set the optional output_noData, if the original file has none set. For example:
`gdal_clip2range.py input.tif output.tif 0 1 0`

This example will clip the range < 0 and > 1, setting the output NoDATA to 0. This example might be used to set a valid range for I/F 32bit floating point image.
