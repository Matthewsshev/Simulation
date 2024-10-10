import sys
import pandas as pd
from shapely import wkb, wkt, geometry, Point, LineString, get_coordinates, distance
import csv
import geojson
from datetime import datetime
import osmnx as ox
# Help Functions

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


# Function to get journeys from the data
def get_journeys(data):
    journeys = []
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
    print(f'All of the journeys from database are found')
    return journeys


# Function to get area of place for analysis
def get_area(name):
    return ox.geocode_to_gdf(name)


def check_rationality(data, journeys, time):
    filtered_journeys = []
    begin = datetime.strptime(time, "%H:%M:%S").time()
    bad = 0
    good = 0
    for journey in journeys:
        if data['mobtype'][journey[-1]] == 'big_stay':
            start_time = datetime.strptime(data['starttime'][journey[-1]], "%Y-%m-%d %H:%M:%S").time()
            if start_time >= begin:
                bad += 1
            else:
                good += 1
    print(f' {bad}  {good}')
    print(f'Percentage {(bad/good) * 100:.2f} %')


def journey_time(data, journeys):
    duration = []
    for journey in journeys:
        start = pd.to_datetime(data['starttime'][journey[0]])
        end = pd.to_datetime(data['endtime'][journey[-1]])
        trip = (end - start).total_seconds() / 86400
        duration.append(trip)
        if trip >= 1:
            print(f'There may be some problem with Data')
    return duration


# Function to check if a point is within a given polygon
def polygon_contains(data, polygon_list):
    gobj = wkt.loads(data)  # Load WKT data to geometry object
    if isinstance(gobj, LineString):
        point = Point(gobj.coords[0])  # Convert LineString to Point using the first coordinate
    else:
        point = gobj
    polygon = geometry.Polygon(polygon_list)  # Create a polygon from the given list of coordinates
    return polygon.contains(point)  # Check if the point is within the polygon


def polygon_intersects(data, polygon_list):
    gobj = wkt.loads(data)
    polygon = geometry.Polygon(polygon_list)
    return polygon.intersects(gobj)


def save_polygon(filename, polygon_s_g, polygon_f_g, polygon_k_g, polygon_m_g):
    with open('analyse/' + filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'geojson'])
        writer.writerow(['polygon_s', geojson.dumps(polygon_s_g)])
        writer.writerow(['polygon_f', geojson.dumps(polygon_f_g)])
        writer.writerow(['polygon_k', geojson.dumps(polygon_k_g)])
        writer.writerow(['polygon_m', geojson.dumps(polygon_m_g)])


def save_journeys(filename, journeys, data):
    with open(f'analyse/' + filename, 'w') as csvfile:
        csvfile.write('name,nr,journey,mobtype,transport,startstep,starttime,endstep,endtime,wkt\n')
        for journey in journeys:
            for mobility in journey:
                csvstr = f'"{data["name"][mobility]}","{data["nr"][mobility]}","{data["journey"][mobility]}","{data["mobtype"][mobility]}",' \
                         f'"{data["transport"][mobility]}","{data["startstep"][mobility]}","{data["starttime"][mobility]}",' \
                         f'"{data["endstep"][mobility]}","{data["endtime"][mobility]}","{data["wkt"][mobility]}"\n'
                csvfile.write(csvstr)


def start_a(data, journeys, polygon_start):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are starting at point a')
    for journey in journeys:
        if cr % 5000 == 0:
            print(cr)
        if polygon_contains(data['wkt'][journey[0]], polygon_start):
            filtered_journeys.append(journey)
        cr += 1
    print(f'All of the journeys have been found')
    return filtered_journeys


def through_b(data, journeys, polygon_middle):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are going through point b')
    for journey in journeys:
        if not polygon_contains(data['wkt'][journey[0]], polygon_middle) and not polygon_contains(data['wkt'][journey[-1]], polygon_middle):
            for trip in journey:
                if polygon_intersects(data['wkt'][trip], polygon_middle):
                    filtered_journeys.append(journey)
                    break  # Break out of the inner loop to avoid adding the same journey multiple times
        if cr % 5000 == 0:
            print(cr)
        cr += 1
    print(f'All of the journeys have been found')
    return filtered_journeys


def end_c(data, journeys, polygon_end):
    filtered_journeys = []
    cr = 0
    print(f'Starting the funktion to get journeys that are ending at the point c')
    for journey in journeys:
        if cr % 5000 == 0:
            print(cr)
        if data['mobtype'][journey[-1]] == 'big_stay' and  polygon_contains(data['wkt'][journey[-1]], polygon_end):
            filtered_journeys.append(journey)
            continue
        cr += 1
    print(f'All of the journeys have been found')

    return filtered_journeys


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
    state = pd.read_csv("a_through_b_c.csv")  # Read the CSV file
    # Define start and end polygons
    hs = get_area('Hochschule Esslingen')
    hs2 = get_area('Mettinger Strasse 127, Esslingen')
    simplified_polygon = hs['geometry'].simplify(tolerance=0.0001)
    simplified_polygon2 = hs2['geometry'].simplify(tolerance=0.0001)
    simplified_single_polygon = simplified_polygon.iloc[0]
    # simplified_single_polygon2 = simplified_polygon2.iloc[0]
    polygon_k = geometry.Polygon(simplified_single_polygon.exterior.coords)
    # polygon_f = geometry.Polygon(simplified_single_polygon2.exterior.coords)
    polygon_s = [(9.263235935155773, 48.76401181283296), (9.261301142916075, 48.76401181283296),
                 (9.261301142916075, 48.765175863995516), (9.263235935155773, 48.765175863995516)]
    # polygon_k = [(9.309117615462673, 48.739325886149096), (9.314213401144736, 48.7392474721196),
    #              (9.314145457335808, 48.736805373966064), (9.308828854274319, 48.73719746194056)]
    polygon_f = [(9.320857096329648, 48.7460642731711), (9.3232907765761, 48.74581435051011),
                 (9.322702304712536, 48.74421613147642), (9.320148935274425, 48.74480149331759)]
    polygon_m = [(9.303664116091152, 48.74002265608213), (9.303664116091152, 48.73697451160857),
                 (9.309056362059602, 48.73697451160857), (9.309056362059602, 48.74002265608213)]
    polygon_s = geometry.Polygon(polygon_s)
    polygon_k = geometry.Polygon(polygon_k)
    polygon_f = geometry.Polygon(polygon_f)
    polygon_m = geometry.Polygon(polygon_m)
    polygon_s_geojson = geojson.Feature(geometry=polygon_s)
    polygon_k_geojson = geojson.Feature(geometry=polygon_k)
    polygon_f_geojson = geojson.Feature(geometry=polygon_f)
    polygon_m_geojson = geojson.Feature(geometry=polygon_m)
    # Convert FeatureCollection to a GeoJSON string
    journeys = get_journeys(state)  # Get all journeys from the data
    flandernstrasse = end_c(state, journeys, polygon_f)
    #  flandernstrasse = through_b(state, flandernstrasse, polygon_m)
    duration = journey_time(state, flandernstrasse)
    print(f"Duration \n {duration}")
    kanalstrasse = end_c(state, journeys, polygon_k)
    print(kanalstrasse)
    check_rationality(state, kanalstrasse, '12:00:00')
    # print(f'Filtered {journeys_start_a_end_b}')
    # print(f'Filtered {filt_1}')
    filename = 'a_through_b_c.csv'
    filename2 = 'a_c.csv'
    filename3 = 'Kanalstrasse.csv'
    filename4 = 'Flanderstrasse.csv'
    filename5 = 'b2.csv'
    csvfile = 'polygon.csv'
    save_polygon(csvfile, polygon_s_geojson, polygon_f_geojson, polygon_k_geojson, polygon_m_geojson)
    save_journeys(filename3, kanalstrasse, state)
    save_journeys(filename4, flandernstrasse, state)


# Entry point of the script
if __name__ == "__main__":
    main()
