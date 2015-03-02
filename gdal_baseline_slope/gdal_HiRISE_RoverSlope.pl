#!/usr/bin/perl -s
###############################################################################
#
#_TITLE  gdal_HiRISE_slope.pl - uses gdaldem and imagemagick to create a 
#              slope image with legend and scale at 1/10 scale. 
#              Needs gdal 1.7.x binaries with python and numpy
#
#_ARGS  
#  input image (most GDAL supported formats)
#  output Jpeg
#
#_USER  Command line entry options [optional parameters]:
#
#   gdal_HiRISE_slope.pl input_DEM.tif 
#
# Requirements:
#       GDAL Library (gdaldem)
#       requires composite from imagemagick
#
#_DESC make colorized slope at 1/10 scale with added legend and scalebar.
#
#_CALL  List of calls:
#       gdaldem
#       composite
#
#_HIST
#       Feb 25 2015 - Trent Hare - original version
#   
#_END
#######################################################################
######################################################################
# For help - user can enter this perl script and return
######################################################################
   if ($#ARGV < 0) {
      print " \n\n          *** HELP ***\n\n";
      print "gdal_HiRISE_slope.pl -  Create 8bit colorized rover baseline slope files with legends and scales, for HiRISE\n\n";
      print "Command line: \n";
      print "gdal_HiRISE_slope.pl input_dem.cub\n";
      print "  The three created output files (baselines 1,2,5) are automatically named\n\n";
      exit 1;
    }

    $input = $ARGV[0];
    chomp $input;
    @fname = split('\.',$input);
    $root = $fname[0];

    @baselines = (1,2,5); 
    ###############################################
    # process baselines 
    ###############################################
    foreach (@baselines) {
      $outSlope  = "adir_".$root."_gdal_0".$_."_0".$_."_ang.tif";
      $outFigure = "adir_".$root."_gdal_0".$_."_0".$_."_ang_mag10_rb20.jpg";
      #if (-e $output) {
         #print "\nOutput file $output Exists! Please remove file and run again.\n\n";
         #exit -1;
      #}
      #calculate baseline slope 1,2,5
      $cmd = "/usgs/cdev/contrib/bin/gdal_baseline_slope.py -baseline ".$_." -ot Byte $input $outSlope";
      print $cmd."\n";
      system($cmd);
  
      #resample to 10m/p using an average method for down-sampling
      $rtmp = $root."xxxtemp_baseline_slope_10m.tif";
      $cmd = "gdalwarp -r average -tr 10 10 $outSlope $rtmp";
      print $cmd."\n";
      system($cmd);
  
      #colorize 
      $ctmp = $root."xxxtemp_baseline_clrslope_10m.png";
      $cmd = "gdaldem color-relief -of PNG $rtmp /usgs/cdev/contrib/bin/slopeRovers_8bit.lut $ctmp";
      print $cmd."\n";
      system($cmd);

      #add existing PNG legend to top left corner
      $ltmp = $root."xxxtemp_baseline_clrslope_10m_legend.tif";
      $cmd = "composite -gravity NorthEast /usgs/cdev/contrib/bin/rover_Slope_legend.png $ctmp $ltmp";
      print $cmd."\n";
      system($cmd);

      #add existing scale bar (only for Mars 10m/p file)
      $cmd = "composite -quality 92 -gravity SouthWest /usgs/cdev/contrib/bin/rover_HiRISE_scalebar.png $ltmp $outFigure";
      print $cmd."\n";
      system($cmd);


      ###############################################
      # clean up
      ###############################################
      unlink($rtmp);
      unlink($ctmp);
      unlink($ltmp);
      unlink($ltmp.".aux.xml");
  
      print "  - files $outSlope and $outFigure created\n\n";
    } 
