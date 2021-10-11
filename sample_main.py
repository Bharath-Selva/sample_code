'''
===============================================================================
			        Search and list image-ids from 
                        planet labe Odata API 
						AUTHOR: Bharath Selvaraj
===============================================================================
Changes:
===============================================================================
			Date			  Author(s)				   Comment
		2021-07-18 :			 BS					 First version
===============================================================================
'''
#===============================================================================
#--- Dependencies
#===============================================================================
#===============================================================================
#------ Python Modules
import argparse, pathlib
#===============================================================================
#===============================================================================
#------ Custom Modules
from sample_utilities import Search_Images
#===============================================================================
#===============================================================================
#------ Global Variable Define
#===============================================================================
#-------------------------------------------------------------------------------


parser = argparse.ArgumentParser(
			prog = 'sample_code.py',
			description = "Search for images to the area of interest(AOI) for a week of the given calendar week of the year with necessary conditions.\n\
				The script designed to search is for a 4Band 3m resolution image with the asset of surface reflectance has permission to download.",
			usage = "%(prog)s <project_code> <year> <week> [options <value>]",
									)
	
parser.add_argument( "project_code", type = str, help ="Project code" )
parser.add_argument( "year", type = int, help = "Search images for the year" )
parser.add_argument( "week", type = int, help = "Search images for the week (Mon - Sun) of the given year" )
parser.add_argument( '--max_cloud', type=float, action='store', default=0.15, help='maximum percent (0.0 - 1.0) of cloud should be in a image [default = 0.15].' )
parser.add_argument( '--area_overlap', type=int, action='store', default=90, help='minimum percent (0 - 100) of area of AOI overlapped on a image [default = 90].' )
parser.add_argument('--data_type', type=str, action='store', default='Product1', choices=['Product1', 'Product2', 'Product1'], help='Currently the script is designed to Product1 (default) images')
parser.add_argument('--config_path', type=pathlib.Path, action='store', default='config.json', help='Path to Config JSON file')
parser.add_argument( '-v', '--version', action='version', version='%(prog)s 1.0' )
for grp in parser._action_groups:
    if grp.title == 'optional arguments' :
        grp.title = 'Options'
    if grp.title == 'positional arguments' :
            grp.title = 'Mandates'
args = parser.parse_args()

in_values = [
    args.project_code,
    args.year,
    args.week,
    args.max_cloud,
    args.area_overlap,
    args.data_type,
    args.config_path
]

print(in_values)
images = Search_Images( in_values )
images.search_ids()

print("Task Completed!")