import sys
import pandas as pd
from shapely import wkb, wkt, geometry, Point, LineString, get_coordinates, distance
import csv
import geojson
from datetime import datetime


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


# Function to check if a point is within a given polygon
def polygon_contains(data, polygon_list):
    gobj = wkt.loads(data)  # Load WKT data to geometry object
    if isinstance(gobj, LineString):
        point = Point(gobj.coords[0])  # Convert LineString to Point using the first coordinate
    else:
        point = gobj
    polygon = geometry.Polygon(polygon_list)  # Create a polygon from the given list of coordinates
    return polygon.contains(point)  # Check if the point is within the polygon


def save_polygon(filename, polygon_s_g, polygon_e_g, polygon_m_g):
    with open('analyse/' + filename,"w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'geojson'])
        writer.writerow(['polygon_s', geojson.dumps(polygon_s_g)])
        writer.writerow(['polygon_e', geojson.dumps(polygon_e_g)])
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


def polygon_intersects(data, polygon_list):
    gobj = wkt.loads(data)
    polygon = geometry.Polygon(polygon_list)
    return polygon.intersects(gobj)


# Function to filter journeys starting and ending within given polygons
def start_a_end_b(data, journeys, polygon_start, polygon_end):
    filtered_journeys = []

    for journey in journeys:
        # Check if the end point of the journey is within the end polygon
        if polygon_contains(data['wkt'][journey[0]], polygon_start) and polygon_contains(data['wkt'][journey[-1]], polygon_end):
            filtered_journeys.append(journey)
    return filtered_journeys


# Function to filter journeys starting within start polygon and intersecting with middle polygon
def start_a_through_b_end_c(data, journeys, polygon_start, polygon_middle, polygon_end):
    filtered_journeys = []
    for journey in journeys:
        if polygon_contains(data['wkt'][journey[0]], polygon_start) and polygon_contains(data['wkt'][journey[-1]], polygon_end):
            for trip in journey:
                if polygon_intersects(data['wkt'][trip], polygon_middle):
                    print(f"Nice")
                    filtered_journeys.append(journey)
                    break  # Break out of the inner loop to avoid adding the same journey multiple times
    return filtered_journeys


def journeys_between_time(data, journeys, begin, end):
    filtered_journeys = []
    begin = datetime.strptime(begin, "%H:%M:%S").time()
    end = datetime.strptime(end, "%H:%M:%S").time()
    print(f"Check {begin}  {end}")
    for journey in journeys:
        time_start = datetime.strptime(data['starttime'][journey[0]], "%Y-%m-%d %H:%M:%S").time()
        time_end = datetime.strptime(data['endtime'][journey[-1]], "%Y-%m-%d %H:%M:%S").time()
        if time_start >= begin and time_end <= end:
            print(f"starttime {time_start}  endtime {time_end}")
            filtered_journeys.append(journey)
    return filtered_journeys

# Function to get journeys from the data
def get_journeys(data):
    journeys = []
    journey = []
    check = data['journey'].tolist()
    prev_jr = check[0]
    cr = 0
    for jr in check:
        if jr != prev_jr:
            journeys.append(journey)
            journey = [cr]
        else:
            journey.append(cr)
        prev_jr = jr
        cr += 1
    journeys.append(journey)  # Append the last journey
    return journeys


# Main function to execute the script
def main():
    state = pd.read_csv("test.csv")  # Read the CSV file
    # Define start and end polygons
    polygon_s = [(9.263235935155773, 48.76401181283296), (9.261301142916075, 48.76401181283296),
                 (9.261301142916075, 48.765175863995516), (9.263235935155773, 48.765175863995516)]
    polygon_e = [(9.258737005359949, 48.73075510927839), (9.262464682864511, 48.730746940607794),
                 (9.262303686826286, 48.72898247655909), (9.258538856390077, 48.729031490286204)]
    polygon_m = [(9.252549602583297, 48.75527785873628), (9.252549602583297, 48.752156270965955),
                 (9.2570071695267, 48.752156270965955), (9.2570071695267, 48.75527785873628)]
    polygon_s = geometry.Polygon(polygon_s)
    polygon_e = geometry.Polygon(polygon_e)
    polygon_m = geometry.Polygon(polygon_m)
    polygon_s_geojson = geojson.Feature(geometry=polygon_s)
    polygon_e_geojson = geojson.Feature(geometry=polygon_e)
    polygon_m_geojson = geojson.Feature(geometry=polygon_m)
    # Convert FeatureCollection to a GeoJSON string
    journeys = get_journeys(state)  # Get all journeys from the data
    filt_1 = journeys_between_time(state, journeys, "22:00:00", "8:00:00")
    journeys_start_a_end_b = start_a_end_b(state, journeys, polygon_s, polygon_e)  # Filter journeys based on polygons
    journeys_start_a_inersects_b_end_c = start_a_through_b_end_c(state, journeys, polygon_s, polygon_m, polygon_e)
    # print(f'Filtered {journeys_start_a_end_b}')
    print(f'Filtered {filt_1}')
    filename = 'a_through_b_c.csv'
    filename2 = 'a_c.csv'
    filename3 = 'time_between.csv'
    csvfile = 'polygon.csv'
    save_polygon(csvfile, polygon_s_geojson, polygon_e_geojson, polygon_m_geojson)
    save_journeys(filename, journeys_start_a_inersects_b_end_c, state)
    save_journeys(filename2, journeys_start_a_end_b, state)
    save_journeys(filename3, filt_1, state)


# Entry point of the script
if __name__ == "__main__":
    main()
