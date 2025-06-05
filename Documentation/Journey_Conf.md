# Journey and Stay Definitions

This document outlines the criteria used to define "Trips," "Stays," and "Journeys" within the simulation or data analysis framework.

---

## Defining a Trip

A trip is defined by any of the following occurrences:

* **Change of Transportation:** A trip is defined each time you switch from one mode of transportation to another. For example, if you start your journey by walking to a bus stop, then take a bus, and finally ride a bike, each of these changes marks the beginning of a new trip segment. This approach helps in breaking down complex journeys into manageable parts for better analysis or tracking.
* **Teleportation:** This occurs when there's a large and sudden discrepancy between two recorded GPS points, suggesting that the object or person has "jumped" from one location to another in an impossibly short time frame. This could be due to a GPS signal glitch, data recording error, or an actual rapid movement (like traveling in a high-speed vehicle). However, when the distance between these two points is abnormally large and doesn't align with any reasonable mode of transportation or time frame, it’s labeled as "teleportation."
* **Change in Time by More Than 1 Second:** This refers to situations where there’s a gap of more than one second between the timestamps of two consecutive GPS coordinates. In GPS tracking, every coordinate is usually recorded with a timestamp.

---

## Defining a Stay

Stays represent pauses in a journey and are categorized based on their duration or context:

* **Big Stay:** This type of stay lasts more than an hour. It’s a significant pause in your journey, like waiting at an airport during a layover, spending time at a restaurant, or any situation where you’re stationary for a prolonged period.
* **Stay:** These are shorter breaks that last between 10 minutes and 1 hour. These could include a quick coffee stop, a brief meeting, or any short break that isn't just a momentary pause but also not long enough to be considered a "big stay."
* **Public Transport Stay:** This is a specific category where the stay happens in the context of public transportation. It could be waiting at a bus stop, train station, or tram stop, and it's defined by the fact that the next leg of your journey involves public transport.

---

## Defining a Journey

A journey is a comprehensive sequence of travel and pauses consisting of various trips and stays. Here’s a detailed breakdown of different journey types:

* **First Journey:** Begins with the first trip and then ends the same as the intermediate journey, with a "Big Stay."
* **Intermediate Journey:** Always starts after a "Big Stay" and also ends with a "Big Stay."
* **Last Journey:** Starts the same as the intermediate journey (after a "Big Stay"), but can end with any type of mobility, such as a trip, a shorter stay, or any other defined movement.