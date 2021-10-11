'''
===============================================================================
				Utilities of class and function used to
			Search and list image-ids from planetLabs Odata API 
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
from planet import api
from planet.api import filters
import rasterio
from rasterio.warp import transform_bounds
import requests
import glob, folium, imageio
import numpy as np
from tqdm import tqdm
#===============================================================================
#===============================================================================
#------ Python Modules
import subprocess, os, json, time
from pprint import pprint
from datetime import datetime
from datetime import timedelta
#===============================================================================
#===============================================================================
#------ Custom Modules
#===============================================================================
#===============================================================================
#------ Global Variable Define
#===============================================================================
#-------------------------------------------------------------------------------

class Search_Images() :
	"""
	It searches images for a week duration of the given area of interest and 
	it also creates a list of image-ids along with it meta-data.
	Using list of image-ids, interactive map is generated. 
	This map is used to decide whether the image to be downloaded for further processing.
	"""

	def __init__( self, input_values ) :
		self.code = input_values[0] 	# Project Code
		self.year = input_values[1]		# Year
		self.week = input_values[2]		# Calendar Week
		self.max_cloud = input_values[3] # max. cloud cover in a image
		self.minarea = input_values[4]	# minimum area of AOI overlap a image
		self.data_type = input_values[5] # Type of Image product default: Product1
		self.config = input_values[6]	 # Path to config JSON file
	
	def proj_path( self ) :
		""" 
		Get project details from the config.json
		and other necessary folder paths.
		Folder Structure and path can be changed based on the preferences.
		Args: 
			proj_path (str): complete path to project folder
			key		       : Access to source provider
			shapefile	   : Geojson shapefile name of Area of Interest (AOI)
		"""
		with open( self.config, 'r' ) as f :
			config = json.loads( f.read() )
		self.key = config[ "key" ]
		self.proj_dir = config[ "proj_path" ]
		self.project = os.path.join( self.proj_dir, self.code )
		aoi = config[ "shapefile" ]
		self.AOI = os.path.join( self.project, "Data", "00_setup", aoi )
		self.outlet = os.path.join( self.project, "Data", "01_source", f"{ self.year }_CW{ self.week }" )
		self.udmpath = os.path.join( self.outlet, "udms" )
		self.thumpath = os.path.join( self.outlet, "thumbnails" )
		self.thum_GR = os.path.join( self.outlet, "thumbnails_GR" )
		self.maps = os.path.join( self.outlet, "interactive_maps" )
		# for x in [self.key, self.proj_dir, self.project, self.AOI, self.outlet, self.udmpath, self.thumpath, self.thum_GR, self.maps]:
		# 	print(f"{x}\n")

	def date_range( self ) :
		"""
		Get start and last date of Calendar Week for the given year
		"""
		startdate = datetime.strptime( f'{ self.year } { self.week } 1', "%Y %W %w" ).date()
		self.startdate = datetime.strftime( startdate, "%Y-%m-%d" )
		lastdate = startdate + timedelta( days=6.9 )
		self.lastdate = datetime.strftime( lastdate, "%Y-%m-%d" )
		# print( f"start date - { self.startdate } \n last date - { self.lastdate }" )

	def api_auth( self ) :
		"""
		Authenticate API-key to access providers DB using planet python library.
		"""
		# Planet client
		self.client = api.ClientV1( api_key = self.key )

	def read_json( self ) :
		"""
		Read the GeoJSON shapefile to get feature details
		"""
		with open( self.AOI ) as json_file :
			self.shape = json.loads( json_file.read() )

	def combine_filters( self ) :
		"""
		Specify and combine filters for the given max. cloud cover and visible percent of AOI on a image.
		This function uses planet library.
		"""
		# Filters
		date_filter = filters.date_range( 'acquired', gte=self.startdate, lte=self.lastdate )   # Date or Timeline filter
		cloud_filter = filters.range_filter( 'cloud_cover', lte=self.max_cloud )   # Cloud coverage for each image (0-1)
		geom_filter = filters.geom_filter( self.shape["features"][0]["geometry"], field_name=None )  # Area of Interest vector coordinates
		area_filter = filters.range_filter( 'visible_percent', gte=self.minarea, lte=100 ) # Area coverage of AOI over a image (0 - 100)

		# Combine filters
		self.filter = filters.and_filter( geom_filter, date_filter, cloud_filter, area_filter )
		# pprint(self.filter)

	def order_udm( self ) :
		"""
		Order single udm via the planet data api.
		This is a submodule of download_udms(), where the logic for the download is set-up.
		"""
		# this is the command to run
		command = [ "planet",
					"--api-key", self.key,
					"data", "download",
					"--item-type", self.data_type,
					"--asset-type", "udm2",
					"--string-in", "id", "{}".format( self.id_ ),
					"--dest", "{}".format( self.udmpath )
				]

		# run it...
		subprocess.run( command )
		
	def download_udms( self ) :
		"""
		This function check and download the UDMs to pre-defined path.
		if all files are not downloaded, It checks again for the files.
		stops when all the files in list are downloaded.
		"""
		print( "Downloading thumbnail images of the image-ids.... " )
		# get list of udm files in folder
		items_in_folder = os.listdir( self.udmpath )
		# check whether all the files are downloaded
		all_there = True
		for one_id in self.result_ids_only :
			if any( one_id in s for s in items_in_folder ) :
				pass
			else:
				all_there = False
				break

		if all_there == True :
			print( "UDMs allready downloaded... skip" )

		# if not, there could files be a downloading or partial download
		# check again for each single id	
		else:
			for id_one in tqdm( self.item_ids,desc="download UDMs" ) :
				# if not, the item is order again
				if not any( id_one in s for s in items_in_folder ) :
					self.id_ = id_one
					# print( 'order', id_one )
					self.order_udm()
					
				else:
					pass
					# print( id_one,"allready there" )

	def get_thumbnails( self ) :
		"""
		Downloads thumbnails for the image-ids available for the given calendar week of the year 
		and area of interest.
		arguments:
		Input - self.search_results
		location - self.thumpath
		"""
		print( "Downloading thumbnail images of the image-ids.... " )
		IMAGE_WIDTH = int (512*4 ) # this is the max resolution we get preview images for
		
		for item in tqdm( self.search_results[ "features" ], desc="download UDMs" ) :
			
			filename = '_'.join( [ item[ 'id' ], item[ 'properties' ][ 'item_type' ] ] )
			
			path_Name = os.path.join( self.thumpath, f"{ filename }.png" )
			
			if not os.path.isfile( path_Name ) :

				thumbnail_url = item[ '_links' ][ 'thumbnail' ]
				response = requests.get( thumbnail_url, auth=( self.key, '' ), params = dict( width = IMAGE_WIDTH ) )
				
				with open( path_Name, 'wb' ) as f :
					f.write( response.content )

	def georefernce_thumbail( self ) :
		"""
		This function is used to geo-reference the thumbnail images from its corresponding udm
		"""
		print( "Geo-referencing the thumbnail images.... " )
		all_udms = glob.glob( os.path.join( self.udmpath,"*.tif" ) )
		
		for udm_name in all_udms :
			
			# To get the corresponding name of a udm and the thumbnail
			planetid = os.path.basename( udm_name ).strip( ".tif" ).strip( "_3B_udm2" )
			allthumbs = glob.glob( os.path.join( self.thumpath, "*.png" ) )
			
			corresp_thumb = [ x for x in allthumbs if planetid in x ]
			assert len(corresp_thumb) == 1
			corresp_thumb = corresp_thumb[0]
		
			# load thumb png 
			thumbimage = imageio.imread( corresp_thumb )

			# turn around to channel first
			temp = []
			for i in range( 4 ) :
				temp.append( thumbimage[ :, :, i ] )
			thumbimage = np.array( temp )
			
			# cut away no data entrys
			band_blue = thumbimage[0]
			band_green = thumbimage[1]
			band_red = thumbimage[2]
			oppac = thumbimage[3]
		
			cutted  = [ band_blue[ ~np.all( band_blue == 0, axis=1 ) ],
					band_green[ ~np.all( band_blue == 0, axis=1 ) ],
					band_red[ ~np.all(band_blue == 0, axis=1 ) ],
					oppac[ ~np.all( band_blue == 0, axis=1 ) ] ]
		
			thumbimage_cutted = np.array( cutted )
			
			# get the georefercing of the udm and save the preview 
			with rasterio.open( udm_name,"r" ) as scr :
		
				# scale image transform
				transform = scr.transform * scr.transform.scale(
					( scr.width / thumbimage_cutted.shape[-1] ),
					( scr.height / thumbimage_cutted.shape[-2] )
				)
		
				out_meta = scr.meta.copy()
				out_meta[ "transform" ] = transform
				out_meta[ "count" ] = 4
				out_meta[ "width" ] = thumbimage_cutted.shape[-1]
				out_meta[ "height"] = thumbimage_cutted.shape[-2]
				
				outlet_current = os.path.join( self.outlet, os.path.basename(corresp_thumb).strip( ".png" ) + ".tif" ) 
				
				with rasterio.open( outlet_current, 'w+', **out_meta ) as dst :
					dst.write( thumbimage_cutted )

	def interactive_map( self ) :
		"""
		Build an interactive map.
		It is used to decide which image id is to be downloaded for further processing.
		"""
		print("Creating iteractive map for the list of image-ids.... ")
		# load the first to initialize the map:
		for png in glob.glob( os.path.join( self.thum_GR, "*" ) ) :
			with rasterio.open( png, "r" ) as scr :
				bbox = transform_bounds( scr.crs, { "init":"epsg:4326" }, *scr.bounds )
				x1,x2,x3,x4 = bbox
				bbox = [ [ x2, x1 ], [ x4, x3 ] ]
			break
		
		# initial map
		m = folium.Map( location = [ x2, x1 ] )

		# loop over all the image's thumbnails
		for udm in glob.glob( os.path.join( self.thum_GR, "*" ) ) :

			with rasterio.open( udm, "r" ) as src :

				# to WGS84
				bbox = transform_bounds( scr.crs, { "init":"epsg:4326" }, *scr.bounds )
				x1,x2,x3,x4 = bbox
				bbox = [ [ x2, x1 ], [ x4, x3 ] ]

				data = scr.read()

				data = np.rollaxis( data, 0, 3 )
				folium.raster_layers.ImageOverlay(
									image=data,
									bounds=bbox,
									opacity = 0.9,
									overlay=True,
									control=True,
									name=os.path.basename(udm),
									).add_to(m)

		folium.GeoJson(self.AOI, name="AOI").add_to(m)
		folium.LayerControl().add_to(m)
		
		m.save( os.path.join( self.maps, "interactive_map.html" ) )


	def search_ids(self):

		self.proj_path()	# Get Folder path
		self.date_range()	# derive Calendar Week's start and last date
		self.read_json()	# read AOI GeoJSON shapefile
		self.api_auth()
		self.combine_filters()

		# 
		req = filters.build_search_request( self.filter, [ self.data_type ] )
		res = self.client.quick_search( req )

		# if there is already the search results for the given calendar week skip the searching 
		# otherwise do the quicksearch
		if not os.path.isfile( os.path.join( self.outlet, "search_results.json" ) ) :
			# try the searching multible times 
			# if its not working the first time
			counter = 0
			while True :
				
				self.search_results = []
				for item in res.items_iter( 1000 ) :
					self.search_results.append( item )

				try :
					
					numberOfItems = len( self.search_results[ "features" ] )
					break
				
				except :
					counter += 1
					time.sleep(2)
					if counter >= 10 :
						raise RuntimeError( 'Failed to fetch data from the planet API, exceeded max. try' )

			print( f"Planet Quicksearch: get { numberOfItems } \
                potential items form API",end="\n" )

			# Save the quick search results as JSON file
			with open(os.path.join( self.outlet, "search_results.json" ), "w+" ) as file :
				json.dump( self.search_results, file )

			# List of only Image-ids from the quick search result.
			self.results_idOnly = [ temp[ "id" ] for temp in self.search_results[ "features" ] ]

			# =============================================================================
			# download the UDM for all the items
			# =============================================================================
			# if not all_udms_are_there:
			if not os.path.isdir( self.udmpath ) :
				os.makedirs( self.udmpath )
			self.download_udms()
			print("List of image-id's UDM are downloaded.")

			# =============================================================================
			# download all the thumbnails for all items
			# =============================================================================
			# if not all_thumbs_are_there:
			if not os.path.isdir( self.thumpath ) :
				os.makedirs( self.thumpath )
			self.get_thumbnails()
			print("List of image-id's thumbnail-image are downloaded.")

			# =============================================================================
			# georeferenced thumbnails:
			# =============================================================================

			if not os.path.isdir(self.thum_GR):
				os.makedirs(self.thum_GR)
				
			self.georefernce_thumbail()
			print("Downloaded thumbnail images are geo-reference to their udms.")

			# =============================================================================
			# interactive maps
			# =============================================================================			

			if not os.path.isdir(self.maps):
				os.makedirs(self.maps)

			self.interactive_map()
			print("Interactive map are created.")
