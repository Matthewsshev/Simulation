The Python script `main.py` includes a function to parse command-line arguments using the `argparse` module. This allows you to customize the number of trips and persons in the simulation by passing arguments when you run the script.

If you need to change map, public transport, etc. Please read `Sumo_config.md`

**Available Arguments:**

* `-t`: Defines the number of trips each person will take in the simulation.
    * **Default:** 10
* `-p`: Defines the number of persons to simulate.
    * **Default:** 1

**To run the simulation with default values:**

```bash
python main.py
```

**To customize the number of trips and persons, use the following format, but without `[]`:**

```bash
python main.py -t [number_of_trips] -p [number_of_persons]
```
# Raw vs. Processed Data Formats

When using the `convert-simsqlite2csv2.py` script, you have the option to output data in either a "raw" format or a "processed" (not raw) format. This distinction is controlled by the `-raw` argument.

---

## Raw Data Format

The **raw data format** (when `-raw` is set to `True`) represents the full, unmanipulated output from the database conversion.

* It includes comprehensive details about **different stays** and is equipped with **journey IDs**.
* This format is designed to be a **1-to-1 replication of the Motiontag format**, meaning it maintains the granular structure and detail characteristic of raw tracking data.
* This format is ideal for users who need the complete, unfiltered dataset for in-depth analysis or for compatibility with systems that expect the Motiontag data structure.

---

## Processed (Not Raw) Data Format

The **processed data format** (when `-raw` is set to `False`, which is the default) is the result of the script applying various transformations and filters to the raw data.

* This format aims to provide a more refined and usable dataset, often incorporating the definitions of "trips" and "stays" as outlined in your `Journey_Conf.md` documentation.
* It typically involves cleaning, categorizing, and potentially summarizing the raw movement data based on parameters like `eraser` (for data holes), `shift` (for realistic zigzags), and `errors` (for simulating data imperfections).
* The processed format is generally more suitable for direct use in simulations, analyses, or visualizations where a cleaner, more interpreted view of movement patterns is required, rather than the raw sensor-level detail.

In essence, the raw format provides fidelity to the original data source (Motiontag), while the processed format offers a more refined and practically useful dataset tailored for your specific simulation or analysis needs.

The Python script, `convert-simsqlite2csv2.py`, is designed to convert raw database data (specifically from `simulation_data` or similar SQLite databases) into a more usable CSV format. The primary function of this script is to process the raw movement data and categorize it into individual **trips** and different types of **stays**, as defined in the `Journey_Conf.md` documentation.
# Explanation of Data Processing Parameters

This document details the purpose and functionality of the `eraser`, `shift`, and `errors` parameters used in the `convert-simsqlite2csv2.py` script, which are designed to make simulated data more realistic.

---

## 1. `errors` Parameter

The `errors` parameter (controlled by the `-err` argument) addresses the realism of the simulation data. By default, the simulation might generate data for every single step, which is not realistic compared to real-world data collection.

* When `errors` is enabled (`-err True`), it ensures that not all data points are saved. This mimics the inherent incompleteness and imperfections of real-world data, providing a more realistic representation.
* **Default Value:** `False` (meaning errors are disabled by default, and all data is saved).

---

## 2. `eraser` Parameter

The `eraser` parameter (controlled by the `-e` argument) is used to introduce "holes" or gaps in the data by deleting a certain percentage of consecutive data points. This simulates scenarios where data might be missing or incomplete in real-world tracking.

The default percentage of points deleted depends on the `occupation` of the simulated individual:

* **`occupation_limits`:**
    * `Pupil`: between 7% and 15%
    * `Student`: between 5% and 10% 
    * `Worker`: between 10% and 20%
  
The `eraser` argument acts as a **multiplier** to adjust these default percentages.
* A value greater than `1` will result in a higher percentage of points being deleted (more holes).
* A value less than `1` will result in a lower percentage of points being deleted (fewer holes).
* **Default Value:** `1.0` (no change to default percentages).

---

## 3. `shift` Parameter

The `shift` parameter (controlled by the `-s` argument) is used to introduce small, realistic variations (zigzags) in the data points by shifting them a few meters. This accounts for minor inaccuracies or natural deviations that can occur in real-life movement tracking (e.g., a person walking slightly off a straight path).

The default percentage for shifting depends on the `transport type`:

* **Public Transport (`pt`)**: The `max_percentage` for shifting is `0.16` (16%).
* **`transport_limits` (for other modes):**
    * `car`: `20%`
    * `bicycle`: `12%`
    * `motorcycle`: `16%`
* If the person is walking, the default percentage is `0.08` (8%).

Similar to the `eraser` argument, the `shift` argument acts as a **multiplier** to adjust these default percentages.
* A value greater than `1` will apply a higher percentage of shifting (more zigzags).
* A value less than `1` will apply a lower percentage of shifting (fewer zigzags).
* **Default Value:** `1.0` (no change to default percentages).

**Available Argument:**
* **`-d`**: Specifies the name of the input database file without the extension.
    * **Default:** `simulation_data_test`
* **`-o`**: Defines the name of the output CSV file or directory.
    * **Default:** `sql2csv`
* **`-e`**: Multiplier for an "eraser" parameter.
    * **Default:** `1.0`
* **`-s`**: Multiplier for a "shift" parameter.
    * **Default:** `1.0`
* **`-err` r`**: Enables or disables error handling.
    * **Default:** `False`
* **`-den`**: Sets the density of points to be processed or included.
    * **Default:** `5`
* **`-raw`**: Choice between outputting raw data or fully processed data.
    * **Default:** `False` 
### Example Usage:

```bash
python convert-simsqlite2csv2.py -d my_simulation_data -o output_folder -err True -den 10
```