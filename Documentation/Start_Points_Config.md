# Definition `osm2csv.py`

The `osm2csv.py` script is a utility designed to bridge the gap between geographic data from OpenStreetMap (OSM) and the SUMO (Simulation of Urban MObility) traffic simulator. Its primary function is to extract specific point-of-interest data from OSM files and convert them into a CSV format containing SUMO "edge" IDs, which are essential for defining routes and locations within a SUMO simulation.

---

### Main Purpose:

At its core, `osm2csv.py` performs the following key operations:

1.  **Parses OSM Files:**
    * It utilizes the `osmium` library to efficiently read and process `.osm` files.
    * These files typically contain comprehensive geographic information, including nodes (points), ways (lines), and relations (groups of elements).

2.  **Extracts Geographic Points:**
    * The script specifically focuses on identifying and extracting valid latitude and longitude coordinates from nodes within the provided OSM files.
    * These nodes commonly represent distinct real-world locations such as houses, schools, parks, or shops, based on the input OSM data.

3.  **Converts to SUMO Edges:**
    * By leveraging SUMO's TraCI (Traffic Control Interface), the script intelligently converts these real-world GPS coordinates (latitude and longitude) into their corresponding SUMO "edge" IDs.
    * In SUMO, an "edge" represents a segment of the road network. This conversion allows agents within the simulation to "spawn" at or interact with specific locations directly on the simulated road network.

4.  **Filters and Saves to CSV:**
    * The converted SUMO edge IDs undergo a filtering process to ensure their validity (e.g., removing any non-numeric or otherwise invalid IDs).
    * Finally, these validated edge IDs are meticulously saved into separate `.csv` files. Each CSV file corresponds to a specific type of location (e.g., `friends.csv`, `shop.csv`, `home.csv`, etc.).

---

### Simulation use:

This `osm2csv.py` script serves as a fundamental component for preparing custom location data within your SUMO simulations. For example:

* If you intend to simulate agents traveling to specific "friends' houses" or "supermarkets," you would first define these precise geographic locations within an OSM file.
* `osm2csv.py` then acts as the translator, taking that raw geographic data and transforming it into the SUMO-understandable edge IDs.
* This seamless translation allows you to directly incorporate your custom points of interest into complex simulation scenarios.

---

### Input and Output:

* **Input:**
    * The script accepts multiple OpenStreetMap (`.osm`) files.
    * Each `.osm` file typically represents a distinct category of points (e.g., `friends.osm`, `shop.osm`, `home.osm`, `work.osm`, `school.osm`, `park.osm`).
    * These input files are provided as command-line arguments when executing the script.

* **Output:**
    * The script generates corresponding `.csv` files (e.g., `friends.csv`, `shop.csv`, `home.csv`).
    * Each `.csv` file contains a clear, organized list of SUMO edge IDs that were derived from its respective input OSM file.

---

### Creating OSM Files:

For detailed instructions on how to create and prepare the necessary `.osm` files specifically for use with this script, please refer to the `Sumo_Config.md` document. This companion document will guide you through the process of setting up your OSM data.