import argparse
import pandas as pd
from shapely import wkt, geometry, Point, LineString, Polygon
from datetime import datetime, timedelta
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.ops import transform
from pyproj import Transformer
import geopandas as gpd
from collections import defaultdict
import numpy as np


# Function to get journeys from the data +
def get_journeys(data):
    journeys = []
    journey = []
    data_inx = data.index
    prev_inx = data_inx[0]
    for inx in data_inx:
        if inx % 5000 == 0:
            print(inx)
        if data['type'][inx] == 'S':
            duration = get_duration(data, inx)
            if duration >= timedelta(hours=1):
                # Start einer neuen Reise, wenn die Dauer >= 1 Stunde ist
                journey.append(inx)
                journeys.append(journey)
                journey = []
            else:
                # Füge den aktuellen Index zur Reise hinzu
                journey.append(inx)
        elif data['userid'][prev_inx] != data['userid'][inx]:
            # Benutzerwechsel prüfen
            if data['type'][prev_inx] == 'S':
                duration = get_duration(data, prev_inx)
                if duration >= timedelta(hours=1):
                    # Alte Reise abschließen und neue beginnen
                    journey = []
            # Neue Reise beginnen (unabhängig von der Dauer)
            if journey:
                journeys.append(journey)
            journey = [inx]
        else:
            # Füge Index der aktuellen Reise hinzu
            journey.append(inx)
        prev_inx = inx
    if journey:
        journeys.append(journey)
    print(f'All of the journeys from database are found')
    return journeys


# Function to get area of place for analysis +
def get_area(name):
    return ox.geocode_to_gdf(name, by_osmid=True)


# Function to get duration of an activity +
def get_duration(data, inx):
    timeformat = "%Y-%m-%d %H:%M:%S"
    start_time = f'{data["started_at_date"][inx]} {data["started_at_time"][inx]}'
    end_time = f'{data["finished_at_date"][inx]} {data["finished_at_time"][inx]}'
    start_time = datetime.strptime(start_time, timeformat)
    end_time = datetime.strptime(end_time, timeformat)
    duration = end_time - start_time
    return duration


# Function to check the rationality of the Trip using departure times +
def check_rationality(data, journeys, time):
    begin = datetime.strptime(time, "%H:%M:%S").time()
    bad = 0
    good = 0
    for journey in journeys:
        duration = get_duration(data, journey[-1])
        if data['type'][journey[-1]] == 'S' and duration >= timedelta(hours=1):
            start_time = datetime.strptime(data['started_at_time'][journey[-1]], "%H:%M:%S").time()
            if start_time >= begin:
                bad += 1
            else:
                good += 1
    print(f' {bad}  {good}')
    if good == 0:
        print(f'There are no trips that was started before {begin}')
    else:
        print(f'Percentage {(bad/good) * 100:.2f} %')



def create_polygon_osm(address):
    area = get_area(address)
    simplified_polygon = area['geometry'].simplify(tolerance=0.0001)
    return simplified_polygon

# Function to create polygon using OSM +
def create_polygon(lon, lat, radius):
    radius = radius / 111320
    points = [(lon - radius, lat - radius),
              (lon + radius, lat - radius),
              (lon + radius, lat + radius),
              (lon - radius, lat + radius),
              (lon - radius, lat - radius)]
    polygon = Polygon(points)
    return polygon


# Function to check if a point is within a given polygon +
def polygon_contains(data, polygon_list):
    if isinstance(data, LineString):
        point = Point(data.coords[0])  # Convert LineString to Point using the first coordinate
    else:
        point = data
    polygon = geometry.Polygon(polygon_list)  # Create a polygon from the given list of coordinates
    return polygon.contains(point)  # Check if the point is within the polygon


# Function to check whether trip intersects  given polygon +
def polygon_intersects(data, polygon_list):
    # gobj = wkt.loads(data)
    polygon = geometry.Polygon(polygon_list)
    return polygon.intersects(data)


# Function to save polygons in geojson format +
def save_polygon(filename, arr):
    with open('analyse/' + filename, "w") as csvfile:
        csvfile.write(f'"id","polygon"\n')
        for inx, polygon in enumerate(arr):
            csvfile.write(f'"polygon_{inx}","{polygon}"\n')


# Function to save journeys in csv +
def save_journeys(filename, journeys, data):
    with open(f'analyse/' + filename, 'w') as csvfile:
        csvfile.write("id,userid,type,mode,geometry,length,timearray,started_at_date,started_at_time,finished_at_date,finished_at_time,confirmed\n")
        for journey in journeys:
            for mobility in journey:
                csvstr = f'"{data["id"][mobility]}","{data["userid"][mobility]}","{data["type"][mobility]}","{data["mode"][mobility]}",' \
                         f'"{data["geometry"][mobility]}","{data["length"][mobility]}","{data["timearray"][mobility]}",' \
                         f'"{data["started_at_date"][mobility]}","{data["started_at_time"][mobility]}","{data["finished_at_date"][mobility]}",' \
                         f'"{data["finished_at_time"][mobility]}","{data["confirmed"][mobility]}"\n'
                csvfile.write(csvstr)


# Function to get all journeys that are starting in polygon +
def start_a(data, journeys, polygon_start):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are starting at point a')
    for journey in journeys:
        if cr % 5000 == 0:
            print(cr)
        if polygon_contains(data['geometry'][journey[0]], polygon_start):
            filtered_journeys.append(journey)
        cr += 1
    print(f'All of the journeys have been found')
    return filtered_journeys


'''def parse_args():
    # Define argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, default='sql2csv.csv')
    # Add argument for output file (-o) with default value analyse.csv
    parser.add_argument('-o', type=str, default='analyse.csv')
    # Add argument for execution of finding journeys which are ending at Polygon a
    parser.add_argument('-e', type=bool, default=False)
    # Add argument for execution of finding journeys which are going through Polygon b
    parser.add_argument('-t', type=bool, default=False)
    # Add argument for execution of finding journeys which are starting at Polygon c
    parser.add_argument('-s', type=bool, default=False)
    # Add argument for Center of Polygon a
    parser.add_argument('-ep', type=float, default=5)
    parser.add_argument('-lon', type=float, default=9.28823)
    parser.add_argument('-lat', type=float, default=48.74276)
    # Parse arguments
    return parser.parse_args()
'''


# Function to get all journeys that have use of two public transports 2 different Buses for example
def two_pt(data, journeys):
    filtered_journeys = []
    print(f'Starting the funktion to get journeys that are having two uses of pt one after another')
    pt = ['bus', 'trolleybus', 'light rail', 'train']
    for journey in journeys:
        cr = 0
        start, end = None, None
        for trip in journey:
            if data['transport'][trip] in pt:
                if cr == 0:
                    start = trip
                else:
                    end = trip
                cr += 1
        if start and end:
            print(f"Time taken on bus {data['starttime'][start]} ss {data['starttime'][journey[-1]]}")
        if cr >= 2:
            filtered_journeys.append(journey)
    return filtered_journeys


def stop_duration(data, trip):
    stop_start = pd.to_datetime(f"{data['started_at_date'][trip]} {data['started_at_time'][trip]}")
    stop_end = pd.to_datetime(f"{data['finished_at_date'][trip]} {data['finished_at_time'][trip]}")
    temp = stop_end - stop_start
    duration = temp.total_seconds() / 60
    return duration


# Function to check how much time does Bus take to complete his Route
def pt_waiting_times(data, journeys, end_point):
    polygon_end = create_polygon(end_point[0], end_point[1], 1000)
    print(f'polygon {polygon_end}')
    pt = ['bus', 'LightRail', 'RegionalTrain']
    journeys_end = end_c(data, journeys, polygon_end)
    journey_end_transport = transport_type(data, journeys_end, pt)
    print(f'End {journey_end_transport}')

    for journey in journey_end_transport:
        duration = stop_duration(data, journey[-1])
        print(f'Duration {duration}')
    b = data
    return b


# Function to get all journeys that are going through Polygon
def through_b(data, journeys, polygon_middle):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are going through point b')
    for journey in journeys:
        if not polygon_contains(data['geometry'][journey[0]], polygon_middle) and not polygon_contains(data['geometry'][journey[-1]], polygon_middle):
            for trip in journey:
                if polygon_intersects(data['geometry'][trip], polygon_middle):
                    filtered_journeys.append(journey)
                    break  # Break out of the inner loop to avoid adding the same journey multiple times
        if cr % 5000 == 0:
            print(cr)
        cr += 1
    print(f'All of the journeys have been found')
    return filtered_journeys


# Function to get all journeys that are ending in Polygon
def end_c(data, journeys, polygon_end):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are ending at the point c')
    for journey in journeys:
        if cr % 5000 == 0:
            print(cr)
        duration = get_duration(data, journey[-1])
        if data['type'][journey[-1]] == 'S' and duration >= timedelta(hours=1) and polygon_contains(data['geometry'][journey[-1]], polygon_end):
            filtered_journeys.append(journey)
            continue
        cr += 1
    print(f'All of the journeys have been found')

    return filtered_journeys


# Classify each journey as 'direct' or 'indirect'
def direct_trip(data, journeys):
    journey_list = defaultdict(int)
    for journey in journeys:
        for trip in journey:
            # Count as 'indirect' if there's a 'stay' point in the journey
            if data['type'][trip] == 'S':
                journey_list['indirect'] += 1
            # Count as 'direct' if it's the last trip in the journey
            elif trip == journey[-1]:
                journey_list['direct'] += 1
    return journey_list


# Calculate transport type usage across journeys
def transport_percentage(data, journeys):
    trans_dict = defaultdict(int)
    pt_list = ['bus', 'trolleybus', 'light rail', 'train']  # Public transport modes
    trans_list = ['passenger', 'bicycle', 'motorcycle']  # Personal transport modes

    for journey in journeys:
        for trip in journey:
            # Only consider valid trips with 'mobtype' as 'trip' and valid 'wkt' coordinates
            if data['type'][trip] == 't' and data['geometry'][trip] != Point("inf", "inf"):
                transport_type = data['mode'][trip]

                # Count as specific personal transport if in trans_list
                if transport_type in trans_list:
                    trans_dict[transport_type] += 1
                    break  # Stop counting after finding a match in this journey
                # Count as 'Public transport' if transport is in pt_list
                elif transport_type in pt_list:
                    trans_dict['Public transport'] += 1
                    break
                # If it's the last trip in the journey, count the specific transport type
                elif trip == journey[-1]:
                    trans_dict[transport_type] += 1

    return trans_dict


# Function to get all journeys between given time
def journeys_between_time(data, journeys, begin, end):
    filtered_journeys = []
    begin = datetime.strptime(begin, "%H:%M:%S").time()
    end = datetime.strptime(end, "%H:%M:%S").time()
    print(f"Starting the funktion to get journeys that are between {begin}  and {end}")
    cr = 0
    for journey in journeys:
        if cr % 5000 == 0:
            print(cr)
        time_start = datetime.strptime(data['starttime'][journey[0]], "%Y-%m-%d %H:%M:%S").time()
        time_end = datetime.strptime(data['endtime'][journey[-1]], "%Y-%m-%d %H:%M:%S").time()
        if time_start >= begin and time_end <= end:
            filtered_journeys.append(journey)
    print(f"All of the journeys have been found")
    return filtered_journeys


# Function to get a length of a journey
def journey_length(data, journeys):
    length = []
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    for journey in journeys:
        s = 0
        for trip in journey:
            # gobj = wkt.loads(data['wkt'][trip])
            distance = transform(transformer.transform, data['wkt'][trip])
            s += distance.length
        # Project the LineString to the new CRS
        # projected_line = transform(transformer.transform, s) / 1000
        length.append(s / 1000)
    return length


# Function to build a Histogram
def histogram_build(trans_dict, title):
    plt.figure(figsize=(10, 6))
    # Create the 2D histogram
    plt.bar(trans_dict.keys(), trans_dict.values())
    # Add color bar
    # Add labels and title
    plt.title(title)

    # Show the plot
    plt.tight_layout()
    plt.show()


def transport_type(data, journeys, transport):
    tranport_journeys = []
    for journey in journeys:
        for trip in journey:
            mode = data['mode'][trip]
            if isinstance(transport, list):
                if mode in transport:
                    tranport_journeys.append(journey)
                    break
            else:
                if mode == transport:
                    tranport_journeys.append(journey)
                    break
    return tranport_journeys


def cruising_speed(data, journeys, quantile):
    journey_cruising = []
    for journey in journeys:
        journey_length = 0
        journey_time = journey_duration(data, journey)
        print(f'Journey duration {journey_time} {journey}')
        for trip in journey[:-1]:
            trip_length = int(data['length'][trip])
            journey_length += trip_length
        journey_speed = int(journey_length / journey_time)
        journey_cruising.append(journey_speed)
    res = np.quantile(journey_cruising, quantile)
    return res


def config_read(data):
    return {
        'start': data['start'][0],
        'through': data['through'][0],
        'end': data['end'][0],
        'input': data['input'][0],
        'output': data['output'][0],
        'polygon_start': data['polygon_start'][0].split(','),
        'polygon_through': data['polygon_through'][0].split(','),
        'polygon_end': data['polygon_end'][0].split(',')
    }


# Function to get duration of a trip
def journey_duration(data, journey):
    journey_start = pd.to_datetime(f"{data['started_at_date'][journey[0]]} {data['started_at_time'][journey[0]]}")
    journey_end = pd.to_datetime(f"{data['finished_at_date'][journey[-2]]} {data['finished_at_time'][journey[-2]]}")
    temp = journey_end - journey_start
    duration = temp.total_seconds() / 60
    return duration


def heatmap_save(polygons, quantile, transport, filename):
    with open('analyse/' + filename, "w") as csvfile:
        csvfile.write(f'"id","polygon","transport","quantile"\n')
        for inx, polygon in enumerate(polygons):
            csvstr = f'"{inx}","{polygon}","{transport}","{quantile[inx]}"\n'
            csvfile.write(csvstr)
    return 5


def heatmap_cruising(filename, data, journeys, transport, quantile_values):
    config = pd.read_csv(filename)
    '''polygons_dict = {i: row['polygon'].split(',') for i, row in config.iterrows()}
    keys = polygons_dict.keys()'''
    polygons_addr = config['polygon']
    quantile_arr = []
    polygons = []
    index = polygons_addr.index
    for inx in index:
        polygon = create_polygon_osm(polygons_addr[inx])
        polygon_journeys = start_a(data, journeys, polygon[0])
        print(f'Polygon Journeys {polygon_journeys}')
        quantile_result = cruising_speed(data, polygon_journeys, quantile_values)
        quantile_arr.append(quantile_result)
        polygons.append(polygon)
    return polygons, quantile_arr



# Main function to execute the script
def main():
    config = pd.read_csv('analyse/config.csv')
    config_tuple = config_read(config)
    state = pd.read_csv(config_tuple['input'])  # Read the CSV file
    state['geometry'] = gpd.GeoSeries.from_wkt(state['geometry'])
    # Define start and end polygons
    addresses = ['R5732233', 'R5732224', 'R5732231', 'R5734257', 'R5732222']
    # test_polygons = create_polygon_osm(addresses)
    result = get_journeys(state)  # Get all journeys from the data
    quantile_values = [0.05, 0.95]
    transport_values = ['passenger', 'bicycle']
    heatmap_journeys = result
    file = 'heatmap_config.csv'
    polygons, quantile = heatmap_cruising('analyse/' + file, state, heatmap_journeys, transport_values[0], quantile_values[0])
    output_file = 'heatmap.csv'
    heatmap_save(polygons, quantile, transport_values[0], output_file)
    if config_tuple['start']:
        start_polygon = create_polygon(float(config_tuple['polygon_start'][0]), float(config_tuple['polygon_start'][1]), int(config_tuple['polygon_start'][2]))
        result = start_a(state, result, start_polygon)
        polygons.append(start_polygon)
    if config_tuple['through']:
        through_polygon = create_polygon(float(config_tuple['polygon_through'][0]), float(config_tuple['polygon_through'][1]), int(config_tuple['polygon_through'][2]))
        result = through_b(state, result, through_polygon)
        polygons.append(through_polygon)
    if config_tuple['end']:
        end_polygon = create_polygon(float(config_tuple['polygon_end'][0]), float(config_tuple['polygon_end'][1]), int(config_tuple['polygon_end'][2]))
        result = end_c(state, result, end_polygon)
        car_journeys = transport_type(state, result, transport_values[0])
        quantile_result = cruising_speed(state, result, quantile_values)

        polygons.append(end_polygon)
    dict_t = transport_percentage(state, result)
    dict_d = direct_trip(state, result)
    # flandernstrasse = two_pt(state, flandernstrasse)
    histogram_build(dict_t, 'Trips with different transport types')
    histogram_build(dict_d, 'Direct/Indirect Trips')
    save_journeys(config_tuple['output'], result, state)
    save_polygon('polygon.csv', polygons)


# Entry point of the script
if __name__ == "__main__":
    main()
