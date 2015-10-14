PlateVertex2Obj.py also called pdsVertexTAB2obj.py

 Purpose: To convert simple 3D PDS Shapemodel or Plate-Vertex to Alias WaveFront OBJ
 Note: This implies the original vertices are listed in sequestial order from 1,2,3,4,...n
 Trent Hare, April 2013
 
Usage: PlateVertex2Obj.py input.tab  output.obj

An example for Eros can be download from here:
http://sbntools.psi.edu/ferret/datasetDetail.action?dataSetId=NEAR-A-MSI-5-EROSSHAPE-V1.0
find the plate-vertex files under: <zip>\NEAR_A_MSI_5_EROSSHAPE_V1_0\data\vertex\
and convert:

 % PlateVertex2Obj.py ver512q.tab ver512q_3D.obj
 
 For a Python environement I recommend Anaconda.
 