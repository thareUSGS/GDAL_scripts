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
#       gdal_baseline_slope.py, gdaldem, gdalinfo, gdal_hist.py, 
#       slope_histogram_cumulative_graph.py 
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
    $root =~ s/_isis3//;

    @baselines = (1,2,5); 
    ###############################################
    # process baselines 
    ###############################################
    foreach (@baselines) {
      $outSlope32  = "32bit_adir_".$root."_gdal_0".$_."_0".$_."_ang.tif";
      $outSlope8  = "adir_".$root."_gdal_0".$_."_0".$_."_ang.tif";
      $outSlope  = "adir_".$root."_gdal_0".$_."_0".$_."_ang.tif";
      $outFigure = "adir_".$root."_gdal_0".$_."_0".$_."_ang_mag10_rb20.jpg";
      #if (-e $output) {
         #print "\nOutput file $output Exists! Please remove file and run again.\n\n";
         #exit -1;
      #}
      #calculate baseline slope 1,2,5
      $cmd = "/usgs/cdev/contrib/bin/gdal_baseline_slope.py -baseline $_ -ot Byte -crop $input $outSlope";
      print $cmd."\n";
      system($cmd);
  
      #calculate stats on 8bit DEM. This helps the gdal_hist with good min/max values
      $cmd = "gdalinfo -stats $outSlope";
      print $cmd."\n";
      system($cmd);
  
      $hist = $root."_adir_".$_."m_hist.xls";
      if (-e $outSlope32) {
         #calculate stats on 32bit_DEM. This helps the gdal_hist with good min/max values
         $cmd = "gdalinfo -stats $outSlope32";
         print $cmd."\n";
         system($cmd);

         #create stats
         #if 32bit file is created, create stats on that file
         $cmd = "/usgs/cdev/contrib/bin/gdal_hist.py -unscale -stats $outSlope32 > $hist";
         print $cmd."\n";
         system($cmd);
      } else {
         #create stats
         $cmd = "/usgs/cdev/contrib/bin/gdal_hist.py -unscale -stats $outSlope > $hist";
         print $cmd."\n";
         system($cmd);
      }

  
      #append histogram in same output as above
      #to make a more attract plot, we will create the histogram on the 8bit truncated version if available
      $cmd = "/usgs/cdev/contrib/bin/gdal_hist.py -unscale -hist $outSlope >> $hist";
      print $cmd."\n";
      system($cmd);

      #plot histogram using Python's matplotlib
      $histPng  = $root."_adir_".$_."m_hist.png";
      $cmd = "/usgs/cdev/contrib/bin/slope_histogram_cumulative_graph.py -name \"$root 0$_\" $hist $histPng";
      print $cmd."\n";
      system($cmd);

      #old gnuplot method
      #$cmd = "echo 'set terminal unknown; plot \"$hist\" using 2:3; set terminal jpeg; set output \"$histJpeg\"; set format y \"%.1t*10^%+02T\";  set arrow 1 nohead from 15,0 to 15,GPVAL_Y_MAX linewidth 1; set key top right;  set tics out; set tmargin 1; plot \"$hist\" using 2:3 with filledcurve lc rgb \"black\" fs solid 0.5 axes x1y1 title \"slope count\",  \"$hist\" using 2:4 lc rgb \"blue\" axes x1y2 title \"cumulative (0 to 100%)\" ' | gnuplot";

  
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
      $cmd = "composite -quality 92 -gravity SouthWest /usgs/cdev/contrib/bin/rover_HiRISE_scalebar_10mp.png $ltmp $outFigure";
      print $cmd."\n";
      system($cmd);


      ###############################################
      # clean up
      ###############################################
      unlink($rtmp);
      unlink($ctmp);
      unlink($ctmp.".aux.xml");
      unlink($ltmp);
      unlink($ltmp.".aux.xml");
  
      print "***  - files $outSlope and $outFigure created\n\n";
    } 
