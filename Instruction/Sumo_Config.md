How to create a sumo simulation using an osm file.
1.Open https://download.geofabrik.de/ and download file in .osm.pbf format. For example I will use Stuttgart region. After that change the name of file if it consist ‘-’ In my example Stuttgart-regbez-latest.osm.pbf  Stuttgart.osm.pbf
2.After that osmium tool extract is needed. Here is how I have installed it
	•download mambaforge here 	https://github.com/condaforge/miniforge/releases/latest/download/Mambaforge-Windows-x86_64.exe
	•while installing it, make sure to select to the "Add Mambaforge to my PATH environment variable"
	•make sure all git bash/powershell/cmd instances are closed
	•open up cmd as admin
	•inside of cmd, type "mamba install osmium-tool", press 'Enter'
	•Osmium should be installed and available to use from anywhere in the command line! Just type "osmium --version" to verify the installation.
3.Exporting a smaller area from an .osm.pbf file and also changing the format to .osm for that 4 coordinate is needed
	•Open https://www.openstreetmap.org/export#map=12/48.7553/9.3214
	•Then use option to manually choose the area
	•After getting the coordinates Open cmd from directory, where .osm.pdf File is. Arrows are showing the order for writing coordinates in the cmd
	•Ussing command ‘osmium extract -b 9.19,48.7,9.43,48.8 stuttgart.osm.pbf -o esslingen.osm’ where  stuttgart.osm.pbf is our file from the beginning and Esslingen.osm is an output file.
4.After that Sumo Saga, that is already installed in Sumo,is needed. The location is: C:\Program Files (x86)\Eclipse\Sumo\tools\contributed\saga if the Sumo isn’t installed then application wouldn’t run properly. Installation guide SUMO: https://sumo.dlr.de/docs/Downloads.php
5.Copy all files from saga to directory with Esslingen.osm file
	•Installing a module to make it work faster pip install rtree
	•After that usin g command python scenarioFromOSM.py --osm esslingen.osm  --out test where out is a folder, which will be created after everything.
6.In the end the folder test is created. Take all the files from that into our project repository and change already existing files in Retrieve and Without_Transport.
7.After that open the OSM.sumocfg file using text redactor or Pycharm and into the <addition files> add file data.rou.xml
8.One of the last steps is to fix the Network file and public transport
	•Open the cmd and write this command,which will fix the Network Problems
	netconvert --osm esslingen.osm -o crr.net.xml --junctions.join-dist 10 --ramps.guess --geometry.remove --osm.stop-output.length 20 --ptstop-output additional.xml --ptline-output ptlines.xml
	• Adjusting Public Transport
	python ptlines2flows.py -n crr.net.xml -s additional.xml -l ptlines.xml -o flows.rou.xml -p 1200 --use-osm-routes --ignore-errors --vtype-prefix pt_ --verbose -e 36000000
	• Changing input files in osm.sumocfg
	osm_pt.rou.xml -> flows.rou.xml 
	(route-files)
	change all additional files to osm_polygons.add.xml, basic.vType.xml, additional.xml, data.rou.xml

9. Then you need to create osm files, that contains data points for School, Unis, Work, etc.
	•School
osmium tags-filter -o school.osm check.osm n/amenity=school --overwrite
	•Friends
osmium tags-filter -o friends.osm check.osm n/amenity=bar,biergarten,cafe,fast_food,food_court,ice_cream,pub,restaurant --overwrite

	•Work
osmium tags-filter -o work.osm check.osm w/landuse=commercial,construction,industrial,retail --overwrite
	•Shop
osmium tags-filter -o shop.osm check.osm n/shop --overwrite
	•Park
osmium tags-filter -o park.osm check.osm wr/leisure=park --overwrite
	•Home
osmium tags-filter -o home.osm check.osm w/landuse=residential --overwrite
10. After that, you need to convert files using osm2csv.py
	This script, main.py, reads OSM files, converts GPS data into SUMO road edges, and saves the results into CSV files. It uses Osmium to process OSM data and Traci to convert GPS coordinates to SUMO edges.
	Arguments:
	he script accepts several command-line arguments to specify the locations of OSM files for various places (friends, shop, home, etc.):
	-f: OSM file for the friends' location
	Default: Without_transport/friends.osm
	-s: OSM file for the shop location
	Default: Without_transport/shop.osm
	-home: OSM file for the home location
	Default: Without_transport/home.osm
	-w: OSM file for the work location
	Default: Without_transport/work.osm
	-sc: OSM file for the school location
	Default: Without_transport/school.osm
	-p: OSM file for the park location
	Default: Without_transport/park.osm
	To specify custom OSM files for different locations:
	python main.py -f custom_friends.osm -s custom_shop.osm -home custom_home.osm -w custom_work.osm -sc custom_school.osm -p custom_park.osm
11.Finally, the code is ready to work with new Map 😊
