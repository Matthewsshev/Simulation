# How to Create a SUMO Simulation Using an OSM File

This guide outlines the process of setting up a SUMO simulation using OpenStreetMap data, from downloading the map to generating various data points for simulation.

---

## 1. Download OSM Data

1.  Open [https://download.geofabrik.de/](https://download.geofabrik.de/) and download a file in `.osm.pbf` format. For example, if you download `Stuttgart-regbez-latest.osm.pbf`, rename it to `Stuttgart.osm.pbf` to remove the hyphen.

---

## 2. Install Osmium Tool

The Osmium tool is essential for processing OSM files. Here's how to install it:

* Download Mambaforge here: [https://github.com/condaforge/miniforge/releases/latest/download/Mambaforge-Windows-x86_64.exe](https://github.com/condaforge/miniforge/releases/latest/download/Mambaforge-Windows-x86_64.exe)
* While installing it, make sure to select "Add Mambaforge to my PATH environment variable".
* Make sure all Git Bash, PowerShell, and CMD instances are closed.
* Open CMD as an administrator.
* Inside CMD, type 
```bash mamba install osmium-tool
``` 
* Osmium should be installed and available to use from anywhere in the command line! Just type `osmium --version` to verify the installation.

---

## 3. Extract Smaller Area and Change Format

To work with a smaller, more manageable area, you can extract a section from an `.osm.pbf` file and also change the format to `.osm`. You will need four coordinates for the bounding box.

1.  Open [https://www.openstreetmap.org/export#map=12/48.7553/9.3214](https://www.openstreetmap.org/export#map=12/48.7553/9.3214).
2.  Then use the option to manually choose the area and note down the coordinates.
3.  After getting the coordinates, open CMD from the directory where the `.osm.pbf` file is located.
4.  Use the command `osmium extract -b 9.19,48.7,9.43,48.8 stuttgart.osm.pbf -o esslingen.osm` where `stuttgart.osm.pbf` is your initial file and `esslingen.osm` is the output file.

---

## 4. SUMO SAGA Tools

SUMO SAGA, which is already installed with SUMO, is needed. Its location is: `C:\Program Files (x86)\Eclipse\Sumo\tools\contributed\saga`. If SUMO isn't installed, the application wouldn't run properly. Installation guide for SUMO: [https://sumo.dlr.de/docs/Downloads.php](https://sumo.dlr.de/docs/Downloads.php).

---

## 5. Prepare SAGA Scenario

1.  Copy all files from the `saga` directory to the directory containing your `esslingen.osm` file.
2.  Install a module to make it work faster:
    ```bash
    pip install rtree
    ```
3.  After that, use the command:
    ```bash
    python scenarioFromOSM.py --osm esslingen.osm --out test
    ```
    Where `test` is a folder which will be created after everything.

---

## 6. Integrate Generated Files

In the end, the folder `test` is created. Take all the files from that into your project repository and change already existing files in `Retrieve` and `Without_Transport`.

---

## 7. Update `OSM.sumocfg`

After that, open the `OSM.sumocfg` file using a text editor or PyCharm and into the `<additional-files>` section, add `data.rou.xml`.

```xml
<configuration>
    <input>
        <net-file value="your_network_file.net.xml"/>
        <route-files value="your_routes.rou.xml"/>
        <additional-files value="data.rou.xml,other_additional_files_here.xml"/>
    </input>
    </configuration>
```

---

## 8. Fix Network File and Adjust Public Transport

1. Fix Network Problems
Open CMD and write this command, which will fix the Network Problems:

```bash
netconvert --osm esslingen.osm -o crr.net.xml --junctions.join-dist 10 --ramps.guess --geometry.remove --osm.stop-output.length 20 --ptstop-output additional.xml --ptline-output ptlines.xml
```
2. Adjusting Public Transport

```bash
python ptlines2flows.py -n crr.net.xml -s additional.xml -l ptlines.xml -o flows.rou.xml -p 1200 --use-osm-routes --ignore-errors --vtype-prefix pt_ --verbose -e 36000000
```

3. Changing Input Files in osm.sumocfg
Change osm_pt.rou.xml to flows.rou.xml within the <route-files> section.
Change all additional-files to osm_polygons.add.xml, basic.vType.xml, additional.xml, data.rou.xml.
```XML
<configuration>
    <input>
        <net-file value="crr.net.xml"/>
        <route-files value="flows.rou.xml"/>
        <additional-files value="osm_polygons.add.xml,basic.vType.xml,additional.xml,data.rou.xml"/>
    </input>
    </configuration>
```

---

## 9. Create OSM Files for Data Points
Then you need to create OSM files that contain data points for School, Universities, Work, etc. These are filtered from your main OSM file (e.g., check.osm).

* School:

```bash
osmium tags-filter -o school.osm check.osm n/amenity=school --overwrite
```

* Friends (Social places):

```bash
osmium tags-filter -o friends.osm check.osm n/amenity=bar,biergarten,cafe,fast_food,food_court,ice_cream,pub,restaurant --overwrite
```

* Work:

```bash
osmium tags-filter -o work.osm check.osm w/landuse=commercial,construction,industrial,retail --overwrite
```

* Shop:

```bash
osmium tags-filter -o shop.osm check.osm n/shop --overwrite
```
* Park:

```bash
osmium tags-filter -o park.osm check.osm wr/leisure=park --overwrite
```

* Home:

```bash
osmium tags-filter -o home.osm check.osm w/landuse=residential --overwrite
```

---

## 11. Convert Files Using osm2csv.py
This script reads OSM files, converts GPS data into SUMO road edges, and saves the results into CSV files. It uses Osmium to process OSM data and Traci to convert GPS coordinates to SUMO edges.

**Available Arguments:**

The script accepts several command-line arguments to specify the locations of OSM files for various places (friends, shop, home, etc.):

* `-f`: OSM file for the friends' location.
	* Default: Simulation/friends.osm
* `-s`: OSM file for the shop location.
	* Default: Simulation/shop.osm
* `-h`: OSM file for the home location.
	* Default: Simulation/home.osm

* -w: OSM file for the work location.
	* Default: Simulation/work.osm

* `-sc`: OSM file for the school location.
	* Default: Simulation/school.osm
* `-p`: OSM file for the park location.

	* Default: Simulation/park.osm
* Example Usage:

**To run the script with default OSM files for different locations:**
```bash
python osm2csv.py 
```
**To specify custom OSM files for different locations:**

```bash
python main.py -f custom_friends.osm -s custom_shop.osm -home custom_home.osm -w custom_work.osm -sc custom_school.osm -p custom_park.osm
```

---

## 12. Conclusion
Finally, the code is ready to work with the new Map 😊