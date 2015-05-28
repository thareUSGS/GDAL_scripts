#!/bin/bash
# add Anaconda 2.0.1 (for GDAL and scipy)
export PATH="/work/users/thare/python/anaconda/bin:$PATH"


echo "gdal_CTX_RoverSlope_crop.pl $1"  | msub  -V -S /bin/bash -d `pwd` -l walltime=72:00:00 -j oe -o LOG_baselineSlope.txt


