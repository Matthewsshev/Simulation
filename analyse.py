import sys
import pandas as pd
from shapely import wkt, geometry, Point, LineString
from datetime import datetime, timedelta
import osmnx as ox
import matplotlib.pyplot as plt
import time
from shapely.ops import transform
from pyproj import Transformer
import geopandas as gpd
from collections import defaultdict
import numpy as np
import sumolib
# influences behavior of csv_reader
maxInt = sys.maxsize
"""
# Adjusting the maximum size limit for reading CSV files to avoid OverflowError.
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)
"""
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


# Function to get journeys from the data +
def get_journeys(data):
    journeys = []
    journey = []
    data_inx = data.index
    prev_inx = data_inx[0]
    for inx in data_inx:
        if inx % 5000 == 0:
            print(inx)

        if data['type'][inx] == 's':
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
            if data['type'][prev_inx] == 's':
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
    """journeys = []
    journey = []
    check = data['journey'].tolist()
    prev_jr = check[0]
    cr = 0
    prev_cr = cr
    print(f'Starting the funktion to get all journeys from database')
    for jr in check:
        if cr % 5000 == 0:
            print(cr)
        if jr != prev_jr or data['name'][cr] != data['name'][prev_cr]:
            journeys.append(journey)
            journey = [cr]
        else:
            journey.append(cr)
        prev_jr = jr
        prev_cr = cr
        cr += 1
    journeys.append(journey)  # Append the last journey
    print(f'All of the journeys from database are found')"""
    print(f'Journeys {journeys}')
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
        if data['type'][journey[-1]] == 's' and duration >= timedelta(hours=1):
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


# Function to get duration of a trip +
def journey_time(data, journeys):
    duration = []
    for journey in journeys:
        start = pd.to_datetime(data['starttime'][journey[0]])
        end = pd.to_datetime(data['starttime'][journey[-1]])
        trip = (end - start).total_seconds() / 3600
        duration.append(trip)
        if trip >= 24:
            print(f'There may be some problem with Data')
    return duration


# Function to create polygon using OSM +
def create_polygon(address):
    area = get_area(address)
    simplified_polygon = area['geometry'].simplify(tolerance=0.0001)
    simplified_single_polygon = simplified_polygon.iloc[0]
    polygon = geometry.Polygon(simplified_single_polygon.exterior.coords)
    return polygon


# Function to check if a point is within a given polygon +
def polygon_contains(data, polygon_list):
   #  gobj = wkt.loads(data)  # Load WKT data to geometry object
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
def save_polygon(filename, polygon_s_g, polygon_f_g, polygon_k_g, polygon_m_g):
    with open('analyse/' + filename, "w") as csvfile:
        csvfile.write(f'"id","polygon"\n')
        csvfile.write(f'"polygon_s","{polygon_s_g}"\n')
        csvfile.write(f'"polygon_f","{polygon_f_g}"\n')
        csvfile.write(f'"polygon_k","{polygon_k_g}"\n')
        csvfile.write(f'"polygon_m","{polygon_m_g}"\n')
        '''writer = csv.writer(csvfile)
        writer.writerow(['id', 'geojson'])
        writer.writerow(['polygon_s', geojson.dumps(polygon_s_g)])
        writer.writerow(['polygon_f', geojson.dumps(polygon_f_g)])
        writer.writerow(['polygon_k', geojson.dumps(polygon_k_g)])
        writer.writerow(['polygon_m', geojson.dumps(polygon_m_g)])
'''


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


# Function to check how much time does Bus take to complete his Route
def pt_time_check(data):
    # data['starttime'] = datetime.strptime(data['starttime'], "%Y-%m-%d %H:%M:%S")
    # data['endtime'] = datetime.strptime(data['endtime'], "%Y-%m-%d %H:%M:%S")
    data_i = data.index
    for transport in data_i:
        time_start = datetime.strptime(data['starttime'][transport], "%Y-%m-%d %H:%M:%S")
        time_end = datetime.strptime(data['endtime'][transport], "%Y-%m-%d %H:%M:%S")
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
        if data['type'][journey[-1]] == 's' and duration >= timedelta(hours=1) and polygon_contains(data['geometry'][journey[-1]], polygon_end):
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
            if data['mobtype'][trip] == 'stay':
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
            if data['mobtype'][trip] == 'trip' and data['wkt'][trip] != Point("inf", "inf"):
                transport_type = data['transport'][trip]

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


"""
# Function to filter journeys starting within start polygon and intersecting with middle polygon
def start_a_through_b_end_c(data, journeys, polygon_start, polygon_middle, polygon_end):
    filtered_journeys = []
    for journey in journeys:
        if polygon_contains(data['wkt'][journey[0]], polygon_start) and polygon_contains(data['wkt'][journey[-1]], polygon_end):
            for trip in journey:
                if polygon_intersects(data['wkt'][trip], polygon_middle):
                    filtered_journeys.append(journey)
                    break  # Break out of the inner loop to avoid adding the same journey multiple times
    return filtered_journeys
"""
"""
# Function to filter journeys starting and ending within given polygons
def start_a_end_b(data, journeys, polygon_start, polygon_end):
    filtered_journeys = []

    for journey in journeys:
        # Check if the end point of the journey is within the end polygon
        if polygon_contains(data['wkt'][journey[0]], polygon_start) and polygon_contains(data['wkt'][journey[-1]], polygon_end):
            filtered_journeys.append(journey)
    return filtered_journeys
"""


# Main function to execute the script
def main():
    print(f"Check")
    state = pd.read_csv("try1.csv")  # Read the CSV file
    state['geometry'] = gpd.GeoSeries.from_wkt(state['geometry'])
    # Define start and end polygons
    addresses = ['R5297117', 'W1319624540', 'R5732233', 'R5732224']
    polygon_k = create_polygon(addresses[0])
    polygon_f = create_polygon(addresses[1])
    polygon_p = create_polygon(addresses[2])
    polygon_i = create_polygon(addresses[3])
    # Convert FeatureCollection to a GeoJSON string
    journeys = get_journeys(state)  # Get all journeys from the data
    flandernstrasse = end_c(state, journeys, polygon_f)
    dict_t = transport_percentage(state, flandernstrasse)
    dict_d = direct_trip(state, flandernstrasse)
    # flandernstrasse = two_pt(state, flandernstrasse)
    # flandernstrasse = through_b(state, flandernstrasse, polygon_p)
    start_t = time.time()
    # flandernstrasse_data = state.loc(np.array(flandernstrasse).flatten())

    kanalstrasse = end_c(state, journeys, polygon_k)
    print(f'kanalstrasse {kanalstrasse}')
    kanalstrasse = start_a(state, kanalstrasse, polygon_i)
    #f_length = journey_length(state, flandernstrasse)
    #f_times = journey_time(state, flandernstrasse)

    #print(f"Journeys length\n {f_length}")
    histogram_build(dict_t, 'Trips with different transport types')
    histogram_build(dict_d, 'Direct/Indirect Trips')

    # print(f'Filtered {journeys_start_a_end_b}')
    # print(f'Filtered {filt_1}')
    filename = 'a_through_b_c.csv'
    filename2 = 'a_c.csv'
    filename3 = 'Kanalstrasse.csv'
    filename4 = 'Flanderstrasse.csv'
    filename5 = 'b2.csv'
    csvfile = 'polygon.csv'
    save_polygon(csvfile, polygon_p, polygon_f, polygon_k, polygon_i)
    save_journeys(filename3, kanalstrasse, state)
    save_journeys(filename4, flandernstrasse, state)
    end_t = time.time()
    exec_t = end_t - start_t
    print(f'Execution Time {exec_t}')


# Entry point of the script
if __name__ == "__main__":
    main()
