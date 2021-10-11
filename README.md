# sample_code
## Search and get list of image-ids
The script search for the images for given time and conditions over an area of interest.

### Description

The sample_main.py needs the input values of project code, and cloud cover and area of interest overlap over an image. 
The script was designed based on the simple project folder structure. The necessary folder path is automatically derived 
internally based on the project code from sample_utilities.py. 

### Requirements
The necessary python modules are needed to run the script mentioned in the requirement.txt file. The Project folder is in Project.rar.

The necessary basic information to execute code are provided in config.json file. This JSON file contains information about 
source providers API-key, location of the project directory and area of interest GeoJSON shapefile's name. GeoJSON shapefile 
should be in *WGS-84* or *EPSG:4326* coordinate reference system and should be *less than 500* vertices point. These two conditions 
are mentioned by the provider. Take caution while changing the project directory path based on the OS environment.

### Execute
The script can executed as 
```py
python .\sample_main.py <project_code> <year> <week> [options <value>]
```

The mandatory arguments should be given are,
* **project_code**(*str*): To identify which project to work on.
* **year**(*int*)        : Which year image you are searching for.
* **Week**(*int*)        : Search images for the *Calendar Week* of the year given.

The optional aarguments have optimal default values. The Values can be given if the image want to be searched in different 
filter conditions. The explaination of the arguments to pass are explained briefly in help message. 

Please use the following command to print help message,
```css
python .\sample_main.py -h
``` 
