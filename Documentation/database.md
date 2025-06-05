# Database: simulation_data

The `simulation_data` database is designed to store various information related to simulated activities, focusing on personal data, transportation modes, and movement patterns for both people and vehicles. It consists of the following 5 tables:

---

## 1. `Personal_Info`

This table includes all personal data about individuals in the simulation, such as their name, type (e.g., student, worker), age, salary, and other relevant demographic details.

---

## 2. `people_type`

This table categorizes individuals based on their type, providing classifications such as:
* Student
* School Pupil
* Worker
* Senior

---

## 3. `pedestrian_data`

This table stores movement data specifically for pedestrians. It includes information such as:
* Person's movement trajectory.
* Transport mode used (e.g., by foot).
* Their speed.

---

## 4. `vehicles`

This table lists all available transport modes within the simulation. Examples include:
* Bicycle
* Motorbike
* Car
* Bus
* Walk
* RegionalTrain
* LightRail

---

## 5. `vehicle_data`

This table is similar to `pedestrian_data` but specifically for vehicles. In addition to movement data and speed, it includes an extra column:
* **CO2 production:** Shows the amount of CO2 produced by the vehicle in milligrams per second (mg/s).