# Configuration File Overview

This document describes the key classes, functions, and adjustable parameters within the simulation configuration, focusing on trip generation, data retrieval, human characteristics, and traffic adjustments.

---

## Class: `Trips`

This class handles the definition and generation of trips within the simulation.

### `List autos[]`

Defines which transport modes a simulated person can use.

### `__init__` function

This function determines if a simulated person will have a vehicle. You can also decide if they will have multiple vehicles or none at all.

### `create_trips` function

This function allows you to define how long stops will last during a trip.

### `pedestrian_retrieval` function

* You can modify the transport ID in the database.
* You can also choose which data about the person will be stored in the database.

### `autos_retrieval` function

Allows you to choose which information about the transport (vehicle) will be saved in the database.

### `delete_all` function

Allows you to decide which data from the last simulation should be deleted from the database.

---

## Class: `Human` and its Subclasses

This class and its subclasses manage the personal details and characteristics of the simulated individuals.

### `__init__` function

You can change the personal details of people, such as their name, home, work, university, school, park, friends' places, age, salary, pocket money, or scholarship.

---

## Main Function

The main function controls overarching simulation parameters.

### Define the number of people

You can modify the `quantity` variable to set how many people will be simulated.

### Categorizing people

Define how many will be workers, students, pupils, or seniors by adjusting values in the `if` statements.

### Number of trips per person

Change the `quantityTrips` value to set how many trips each person will take in the simulation.

### Simulation time

The overall simulation time can be set in the final `while` statement.

---

## Traffic Adjustment for Realism

To make the simulation more realistic, especially when simulating a small population (e.g., 10 people), roads may appear empty. A solution is to create background traffic by adding non-user vehicles.

The `trips.trips.xml` file, generated using `randomTrips.py`, includes 50 'flows'. By adjusting the `period='x'` value, the number of cars on the road changes. The `period` defines how often (in seconds) a new car starts a trip. For larger simulations, like with 500 people, you might reduce the number of vehicles to avoid overcrowding.