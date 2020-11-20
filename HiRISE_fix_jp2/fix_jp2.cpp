/*
** fix_jp2
**
** Author: Frank Warmerdam <warmerdam@pobox.com>
**
** License: This program is placed in the public domain.
**
** Purpose: This program attempts to modify the CenterLatGeoKey tag
** in a GeoTIFF or GeoJP2 image file to be StandardParallel1GeoKey.  This is
** primarily valuable to fix up GeoJP2's mistakenly generated with 
** the incorrect parameters for the Equirectangular projection per:
**
**   http://trac.osgeo.org/gdal/ticket/2706
**
** Caveats: 
**  - This only works on little endian TIFF/GeoTIFF data. 
**  - It does not confirm that the file is Equirectangular.
**  - The GeoTIFF data needs to be in the first 10k of the file.
**
** It should do nothing for files that do not contain geotiff info
** or that do not have the CenterLatGeoKey. 
*/

#include <stdio.h>
#include <stdlib.h>

int main( int argc, char ** argv )

{
    if( argc != 2 )
    {
        fprintf( stderr, "Usage: fix_jp2 targetfile.jp2\n" );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Open file.                                                      */
/* -------------------------------------------------------------------- */
    FILE *fp;

    fp = fopen( argv[1], "rb+" );
    if( fp == NULL )
    {
        fprintf( stderr, "ERROR: Failed to open file: %s\n", argv[1] );
        exit( 1 );
    }
    
/* -------------------------------------------------------------------- */
/*      Read a goodly chunk of header.                                  */
/* -------------------------------------------------------------------- */
    unsigned char header[10000];
    int header_bytes;
    int big_endian = 0;

    header_bytes = fread( header, 1, sizeof(header), fp );
    
/* -------------------------------------------------------------------- */
/*      Scan ahead for the beginning of the geotiff within the uuid     */
/*      box.                                                            */
/* -------------------------------------------------------------------- */
    int i;
    int tiff_start = -1;

    for( i = 0; i < header_bytes - 4; i++ )
    {
        if( header[i] == 0x49 
            && header[i+1] == 0x49 
            && header[i+2] == 0x2a
            && header[i+3] == 0x00 )
        {
            tiff_start = i;
            big_endian = 0;
        }

        if( header[i] == 0x4d 
            && header[i+1] == 0x4d
            && header[i+2] == 0x00
            && header[i+3] == 0x2a )
        {
            tiff_start = i;
            big_endian = 1;
        }
    }

    if( tiff_start == -1 )
    {
        fprintf( stderr, "ERROR: Did not find TIFF header.\n" );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Leap to the start of the directory.                             */
/* -------------------------------------------------------------------- */
    int dir_offset;

    if( !big_endian )
        dir_offset = header[tiff_start+4] 
            + header[tiff_start+5] * 256 
            + header[tiff_start+6] * 256 * 256
            + header[tiff_start+7] * 256 * 256 * 256
            + tiff_start;
    else
        dir_offset = header[tiff_start+7] 
            + header[tiff_start+6] * 256 
            + header[tiff_start+5] * 256 * 256
            + header[tiff_start+4] * 256 * 256 * 256
            + tiff_start;

    if( dir_offset < 0 || dir_offset > header_bytes - 50 )
    {
        fprintf( stderr, "ERROR: TIFF directory offset is odd: %d\n", 
                 dir_offset );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      How many tags in the directory?                                 */
/* -------------------------------------------------------------------- */
    int dircount;

    if( !big_endian )
        dircount = header[dir_offset] + header[dir_offset+1] * 256;
    else
        dircount = header[dir_offset+1] + header[dir_offset] * 256;
        
    if( dircount * 12 + dir_offset + 2 > header_bytes )
    {
        fprintf( stderr, "ERROR: We do not seem to have all %d tags of the directory.\n", 
                 dircount );
        exit( 1 );
    }

#ifdef notdef

    TIFF directory entries look like this:

typedef	struct {
	uint16		tdir_tag;	/* see below */
	uint16		tdir_type;	/* data type; see below */
	uint32		tdir_count;	/* number of items; length in spec */
	uint32		tdir_offset;	/* byte offset to field data */
} TIFFDirEntry;

#endif /* def notdef */

/* -------------------------------------------------------------------- */
/*      Scan through the directory looking for tag 34735                */
/*      (TIFFTAG_GEOKEYDIRECTORY).                                      */
/* -------------------------------------------------------------------- */
    int i_entry;
    int tag_offset = -1;

    for( i_entry = 0; i_entry < dircount; i_entry++ )
    {
        int tag;

        if( !big_endian )
            tag = header[i_entry*12 + dir_offset + 2 + 0] 
                + header[i_entry*12 + dir_offset + 2 + 1] * 256;
        else
            tag = header[i_entry*12 + dir_offset + 2 + 1] 
                + header[i_entry*12 + dir_offset + 2 + 0] * 256;

        if( tag == 34735 )
            tag_offset = i_entry*12 + dir_offset + 2;
    }

    if( tag_offset == -1 )
    {
        fprintf( stderr, "ERROR: Failed to find GEOKEYDIRECTORY tag.\n" );
        exit( 1 );
    }
    
/* -------------------------------------------------------------------- */
/*      Confirm key type - should be SHORT (3).                         */
/* -------------------------------------------------------------------- */
    int tag_type;

    if( !big_endian )
        tag_type = header[tag_offset + 2] 
            + header[tag_offset + 3] * 256;
    else
        tag_type = header[tag_offset + 3] 
            + header[tag_offset + 2] * 256;

    if( tag_type != 3 )
    {
        fprintf( stderr, "ERROR: GEOKEYDIRECTORY tag type not SHORT (%d).\n",
                 tag_type );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Collect the value count and offset.                             */
/* -------------------------------------------------------------------- */
    int geokey_count, geokey_offset;

    if( !big_endian )
    {
        geokey_count = header[tag_offset + 4] 
            + header[tag_offset + 5] * 256
            + header[tag_offset + 6] * 256 * 256
            + header[tag_offset + 7] * 256 * 256;
        geokey_offset = header[tag_offset + 8] 
            + header[tag_offset + 9] * 256
            + header[tag_offset + 10] * 256 * 256
            + header[tag_offset + 11] * 256 * 256
            + tiff_start;
    }
    else
    {
        geokey_count = header[tag_offset + 7] 
            + header[tag_offset + 6] * 256
            + header[tag_offset + 5] * 256 * 256
            + header[tag_offset + 4] * 256 * 256;
        geokey_offset = header[tag_offset + 11] 
            + header[tag_offset + 10] * 256
            + header[tag_offset + 9] * 256 * 256
            + header[tag_offset + 8] * 256 * 256
            + tiff_start;
    }

    if( geokey_offset < 0 || geokey_offset + 2 * geokey_count > header_bytes )
    {
        fprintf( stderr, 
                 "ERROR: geokey offset is outside our loaded header: %d\n",
                 geokey_offset );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Scan through the geokeys, searching for 3089 (CenterLatGeoKey). */
/* -------------------------------------------------------------------- */
    int target_offset = -1;

    for( i = 0; i < geokey_count; i++ )
    {
        int tag_value;

        if( !big_endian )
            tag_value = header[geokey_offset + i*2 + 0]
                + header[geokey_offset + i*2 + 1] * 256;
        else
            tag_value = header[geokey_offset + i*2 + 1]
                + header[geokey_offset + i*2 + 0] * 256;

        if( tag_value == 3089 )
            target_offset = geokey_offset + i*2 + 0;
    }

    if( target_offset == -1 )
    {
        fprintf( stderr, 
                 "ERROR: Unable to find target tag (3089 / CenterLat)\n" );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Modify tag, change to 3078 / StdParallel1GeoKey.                */
/* -------------------------------------------------------------------- */

    if( !big_endian )
    {
        header[target_offset] = (unsigned char) (3078 % 256);
        header[target_offset+1] = (unsigned char) (3078 / 256);
    }
    else
    {
        header[target_offset+1] = (unsigned char) (3078 % 256);
        header[target_offset] = (unsigned char) (3078 / 256);
    }

/* -------------------------------------------------------------------- */
/*      Write this bit back to disk.                                    */
/* -------------------------------------------------------------------- */
    if( fseek( fp, target_offset, SEEK_SET ) != 0 )
    {
        fprintf( stderr, "ERROR: fseek(%d) failed.\n", target_offset );
        exit( 1 );
    }

    if( fwrite( header + target_offset, 1, 2, fp ) != 2 )
    {
        fprintf( stderr, "ERROR: fwrite() of 2 bytes failed at %d.\n", 
                 target_offset );
        exit( 1 );
    }

/* -------------------------------------------------------------------- */
/*      Success!  Report and cleanup.                                   */
/* -------------------------------------------------------------------- */
    fclose( fp );
    
    fprintf( stdout, "Success, file updated.\n" );
}
