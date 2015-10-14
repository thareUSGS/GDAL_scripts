#!/usr/bin/env python
#Name: PlateVertex2Obj.py ( or pdsVertexTAB2obj.py )
#Description: To convert simple PDS Shapemodel or Plate-Vertex to Alias WaveFront OBJ
#Note: This implies the original vertices are listed in sequestial order from 1,2,3,4,...n
# Trent Hare, April 2013
import sys, os

def Usage():
    print '''
    This script converts a simple Shapemodel or Plate-Vertex to Alias Wavefront OBJ
    
    Usage: %s <input.tab> <output.obj>
    ''' % (sys.argv[0])
    
if len(sys.argv) < 3:
    Usage()
    sys.exit(0)

#Create the output datasource
try:
    output = sys.argv[2]
except:
    Usage()
    sys.exit(1)

#Open the PDS tab file to read
try:
    input = sys.argv[1]
except:
    Usage()
    sys.exit(1)

infile = open(input, 'r')

#Create an empty file
outfile = open(output, 'w')

#Loop through the input
i = 0
for line in infile:
    if (i == 0):
        nVerts, nFaces = line.split()
        print 'number of vertices: ' + nVerts + '  //  number of faces: ' + nFaces
        print '\tconverting file - please wait...'
        nVerts = int(nVerts)
        nFaces = int(nFaces)
    else:
        l1, l2, l3, l4 =  line.split()
        if i < int(nVerts):
            outfile.write('v ' + l2 + ' ' + l3 + ' ' + l4 + '\n')
        else:
            outfile.write('f ' + l2 + ' ' + l3 + ' ' + l4 + '\n')
    i = i + 1

outfile.close
print '\nObj file: ' + output + ' successfully created.'

