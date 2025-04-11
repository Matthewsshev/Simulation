# convert-sqlite2csv.py
# Convert SQLITE-DB file to CSV and SQLITE-DB file with additional information
# and with tracks removed that cannot be properly anonymised (e.g. holidays)
# ATTENTION: Adds data to the original SQLITE-DB!
# Dominik Schoop, 25.02.2024
import random
import sys
import csv
import datetime
import binascii # hexlify
from shapely import wkb, wkt, geometry, Point, LineString, get_coordinates, distance
from shapely.ops import transform
from pyproj import Transformer
import sqlite3
import argparse


## Global vars

debug = False


## Helper Functions ###############################################

# determine maximal integer on system
# infulences behaviour of csv_reader
maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # until the OverflowError occurs.
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)


# open SQLITE3 database
def openDB(dbname):
    con = sqlite3.connect(dbname)
    return con
def parse_args():
    # Define argument parser
    parser = argparse.ArgumentParser()
    # Add argument for database name without extension with default value simulation_data_test
    parser.add_argument('-d', type=str, default='simulation_data')
    # Add argument for output file (-p) with default value sql2csv
    parser.add_argument('-o', type=str, default='sql2csv')
    # Add argument for eraser multiplication with default value 1
    parser.add_argument('-e', type=float, default=1)
    # Add argument for shift multiplication with default value 1
    parser.add_argument('-s', type=float, default=1)
    # Add argument for enabling Errors with default value true
    parser.add_argument('-err', type=bool, default=False)
    # Add argument for density of Points
    parser.add_argument('-den', type=int, default=5)
    # Add argument for choice between raw and full data
    parser.add_argument('-raw', type=bool, default=False)
    # Parse arguments
    return parser.parse_args()
# Convert simulation step into datetime string starting at a base time
# basetime = string of format dd.mm.yyyy hh:mm:ss
# simulationstep = string of integer, starting at 1
def simulationstep2datetimestr(basetimestr, simulationstepstr):
    timeformat = "%Y-%m-%d %H:%M:%S"
    basetime = datetime.datetime.strptime(basetimestr, timeformat)
    simulationstep = int(simulationstepstr) - 1
    new_time = basetime + datetime.timedelta(seconds=simulationstep)
    new_time.strftime(timeformat)
    time = new_time.time()
    date = new_time.date()
    return time, date


# Construct from a list of Points a string in WKT or WKB format
def coordinates2WKT(coordinates, geoformat="WKT"):
    wktstr = None
    num = len(coordinates)
    length = 0
    if num > 1:  # coordinates form trajectory
        if num > 2500 and geoformat == 'WKB':
            print("WARNING: Number of coordinates might be too large. It is suggested to change to the WKT format.")
        if geoformat == 'WKT':
            wktstr = LineString(coordinates)
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
            projected_line = transform(transformer.transform, wktstr)
            length = int(projected_line.length)
            wktstr = wktstr.wkt
        elif geoformat == 'WKB':
            wktstr = LineString(coordinates).wkb
    else:  # coordinates is single point
        if geoformat == 'WKT':
            wktstr = coordinates[0].wkt
        elif geoformat == 'WKB':
            wktstr = coordinates[0].wkb
    if geoformat == 'WKB':
        # convert binary string into string with hex chars
        wktstr = str(binascii.hexlify(wktstr))
        wktstr = wktstr[2:-1]
    return wktstr, length


# Convert individual coordinates of all persons in trips and stays in the format WKB.
# A trip starts or ends when
# a) there are no previous/later coordinates
# b) the mode of transport changes
# c) there is no movement for x simulation steps
# A trip and a stay has a timestamp as start and as end, e.g. 2018-09-01 00:00
# The simulation steps (one second each) are converted into time stamps starting at starttime.
# CSV attributes: person, type (trip or stay), start, end, POINT or LINESTRING (WKT)
# When the trip is quite long (ca. 3000 coordinates) Kepler.gl fails to load with error message "too much recursion".
# Therefore, with the parameter stepjump only every xth coordinate can be considered here.
# 5 persons x 1 trip = 124 KB WKB, 141 KB WKT (-13% WKB vs WKT)
# 1000 persons x 1 trip = 70128 KB WKB, 80180 KB WKT (-13% WKB vs WKT)
# CREATE TABLE pedestrian_data (
#   name VARCHAR (5) NOT NULL,
#   transport INTEGER NOT NULL REFERENCES vehicles (id),
#   datetime INTEGER NOT NULL,
#   lat DOUBLE NOT NULL,
#   lon DOUBLE NOT NULL,
#   speed DOUBLE NOT NULL);
def convertSQLtoWKT(dbinname, csvname, basetime, eraser, shift, error, density=1, stepjump=1, geoformat='WKT', personlist=[]):
    # open database to read
    con = openDB(dbinname)
    cur = con.cursor()  # to read data
    cur2 = con.cursor()
    if density == 1:
        res = 0
    else:
        res = 1
    # get curser to simulated coordinates
    sql_cmd = ("SELECT   p.name, v.name AS transport, datetime, lat, lon, speed "
               "FROM pedestrian_data AS p, vehicles AS v "
               f"WHERE transport = v.id and lat != 'inf'")  # and MOD(p.datetime, {density}) = {res}  was deleted
    sql_cmd2 = ('Select pi.id, pt.Type as Occupation '
                'From personal_Info As pi '
                'Join people_type As pt On pt.id = pi.type_id')
    if len(personlist) > 0:
        plist = '\',\''.join(personlist)
        plist = '\'' + plist + '\''
        whereclause = ' AND p.name IN (' + plist + ')'
        sql_cmd += whereclause
    sql_cmd += " ORDER BY p.name, datetime"
    print(sql_cmd)
    res = cur.execute(sql_cmd)
    res2 = cur2.execute(sql_cmd2)
    info = res2.fetchone()
    # print(f"RES: \n{info}")
    coordinate = res.fetchone()
    # open csvfile
    with open(csvname, "w") as csvfile:
        # write heading
        csvfile.write("id,userid,journey,type,mode,geometry,length,timearray,started_at_date,started_at_time,finished_at_date,finished_at_time,confirmed\n")
        # loop through all simulated coordinates
        stepctr = 0  # for each trip/stay (per person) the steps 1,2,3,...
        ctr = 0
        journey = 1
        # store first data line as previous data
        name_prev = coordinate[0]
        transport_prev = coordinate[1]  # string such as "on foot", "bus", ...
        simulationstep_prev = coordinate[2]  # min is 1
        startsimulationstep = simulationstep_prev
        point_prev = Point(coordinate[4], coordinate[3])  # shapely object
        lat_prev = coordinate[4]
        stop_end = None  # variable for end of stop
        if error:
            print(f'Errors will be added')
        else:
            print(f'Simulation Data will be saved without adding errors')
        transport_trip_prev = transport_prev
        coordinates = []  # list of all points of a trip/stay'
        timearr = []  # list of time for every point
        nr = 0  # consecutive number of trip/stay of one person
        stop = 0  # counter for stop time
        erase_prob = eraser_percentages(info[1], eraser)
        mob_list = ["T", "S", "Ps", "Bs"]  # trip and stay
        public_transport_list = ["bus", "trolleybus", "light rail", "train"]
        inf = 0
        while coordinate:
            ctr += 1
            stepctr += 1
            # print out some progress information
            if ctr % 5000 == 0:
                print(ctr)
            # Read current data and check for end of trip or stay
            name = coordinate[0]
            transport = coordinate[1]
            simulationstep = coordinate[2]
            lat = coordinate[4]
            point = Point(coordinate[4], coordinate[3])  # shapely object
            # Getting a stop with time more than 600 sec
            if lat == lat_prev and name == name_prev and lat_prev != 'inf' and transport_prev == transport:
                stop += 1
            elif stop >= 600 and lat != lat_prev:
                stop_end = True
                print(f"Stop for {name_prev} at {simulationstep_prev} for {stop}")
            else:
                stop = 0

            # End trip if
            # a) user name changes
            # b) transport mode changes
            # c) there is a stop with time > 600 (not implemented yet)
            # d) there is an unreasonable jump in position > 100m (not implemented yet)
            if name != name_prev or stop_end or transport_prev != transport or simulationstep - simulationstep_prev > 1 :
                if distance(point, point_prev) > 0.001:
                    print(f'Person {name_prev} jumping about!')
                nr += 1
                if stop_end:
                    if transport_prev != transport_trip_prev or transport_prev == transport_trip_prev or transport_prev != transport:
                        if simulationstep_prev - stop != startsimulationstep:
                            # write first trip before stay if stay is 1 activity
                            mobtype = mob_list[0]
                            # getting trip data without stay
                            # print(f"Name {name_prev}   unterschied {simulationstep_prev - stop}  {startsimulationstep}")
                            trip = coordinates[:-stop]
                            triptime = timearr[:-stop]
                            trip = density_remove(trip, density)
                            triptime = density_remove(triptime, density)
                            if error:
                                trip, triptime = percentages_remove(trip, triptime, erase_prob)
                                percent = shift_percentage(transport_prev, shift)
                                trip = data_shift(trip, percent)
                            wktstr, length = coordinates2WKT(trip, geoformat)
                            # adjusting time for trip
                            simulationstep_prev -= stop + 1
                            starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                            endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                            csvstr = f'"{nr}","{name_prev}","{journey}","{mobtype}","{transport_prev}","{wktstr}","{length}","{triptime}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                            csvfile.write(csvstr)
                            startsimulationstep = simulationstep_prev + 1
                            if name != name_prev:
                                simulationstep_prev += stop + 1
                            else:
                                simulationstep_prev = simulationstep - 1
                            nr += 1

                    if transport in public_transport_list and transport_prev not in public_transport_list:
                        mobtype = mob_list[2]
                    elif stop <= 3600:
                        mobtype = mob_list[1]
                    else:
                        mobtype = mob_list[3]
                    timearr = timearr[-stop:]
                    timearr = density_remove(timearr, density)
                    # definition of point where stay is
                    stop_end = False
                    stop = 0
                    wktstr, length = coordinates2WKT([point_prev], geoformat)
                else:
                    mobtype = mob_list[0]
                    coordinates = density_remove(coordinates, density)
                    timearr = density_remove(timearr, density)
                    if error:
                        coordinates, timearr = percentages_remove(coordinates, timearr, erase_prob)
                        percent = shift_percentage(transport_prev, shift)
                        coordinates = data_shift(coordinates, percent)
                        print(f'Data shift was done for {name_prev}')
                    print(f' name {name_prev}  len {len(coordinates)} type {mobtype}  coord {coordinates}')

                    wktstr, length = coordinates2WKT(coordinates, geoformat)



                # Add coordinate as the last one if not coordinate of next user
                # if name == name_prev:
                #    coordinates.append(point)
                stepctr = 0
                # Convert time objects into time strings
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                if mobtype == mob_list[0]:
                    mode = transport_prev
                else:
                    mode = ''
                # NO SPACE AFTER COMMA!
                csvstr = f'"{nr}","{name_prev}","{journey}","{mobtype}","{mode}","{wktstr}","{length}","{timearr}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                csvfile.write(csvstr)
                if mobtype == mob_list[3]:
                    journey += 1
                coordinates = []  # start new trip
                timearr = []
                transport_trip_prev = transport_prev
                coordinates.append(point)
                timearr.append(simulationstep)
                if stop >= 600:
                    startsimulationstep = simulationstep_prev
                else:
                    startsimulationstep = simulationstep
                # If change of user store current coordinate and reset trip/stay number and change
                # transport for previous trip
                if name != name_prev:
                    journey = 1
                    transport_trip_prev = transport
                    info = res2.fetchone()
                    if info[0] != name:
                        print(f"????")
                    erase_prob = eraser_percentages(info[1], eraser)
            else:
                # consider only every stepjump time the current point
                if stepctr % stepjump == 0:
                    coordinates.append(point)
                    timearr.append(simulationstep)
            name_prev = name
            transport_prev = transport
            simulationstep_prev = simulationstep
            point_prev = point
            lat_prev = lat
            coordinate = res.fetchone()
        # end of loop, write last trip to file
        if stop >= 600:
            print(f"Stop for {name_prev} at time {startsimulationstep} for {simulationstep_prev - stop}")
            if simulationstep_prev - stop != startsimulationstep:
                nr += 1
                mobtype = mob_list[0]
                # Getting trip data without stay
                trip = coordinates[:-stop]
                triptime = timearr[:-stop]
                trip = density_remove(trip, density)
                triptime = density_remove(triptime, density)
                if error:
                    trip, triptime = percentages_remove(trip, triptime, erase_prob)
                    percent = shift_percentage(transport_prev, shift)
                    trip = data_shift(trip, percent)
                wktstr, length = coordinates2WKT(trip, geoformat)

                # Adjusting time for trip
                simulationstep_prev -= stop
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                csvstr = f'"{nr}","{name_prev}","{journey}","{mobtype}","{transport_prev}","{wktstr}","{length}","{triptime}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                csvfile.write(csvstr)
                startsimulationstep = simulationstep_prev
                simulationstep_prev = simulationstep
            if stop <= 3600:
                mobtype = mob_list[1]
            else:
                mobtype = mob_list[3]
            timearr = timearr[-stop:]
            timearr = density_remove(timearr, density)
            wktstr, length = coordinates2WKT([point_prev], geoformat)
        else:
            mobtype = mob_list[0]
            coordinates = density_remove(coordinates, density)
            timearr = density_remove(timearr, density)
            if error:
                coordinates, timearr = percentages_remove(coordinates, timearr, erase_prob)
                percent = shift_percentage(transport_prev, shift)
                coordinates = data_shift(coordinates, percent)
                print(f'Data shift was done for {name_prev}')
            wktstr, length = coordinates2WKT(coordinates, geoformat)
        starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
        endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
        nr += 1
        # NO SPACE AFTER COMMA!
        csvstr = f'"{nr}","{name_prev}","{journey}","{mobtype}","{transport_prev}","{wktstr}","{length}","{timearr}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
        if mobtype == mob_list[3]:
            journey += 1
        csvfile.write(csvstr)
        print(f"Try {inf}")
    con.close()
    print(ctr)
    print("finished")


def eraser_percentages(occupation, multiplier):
    occupation_limits = {
        "Pupil": (0.07, 0.15),
        "Student": (0.05, 0.1),
        "Worker": (0.1, 0.2)
    }

    min_val, max_val = occupation_limits.get(occupation, (0.2, 0.3))
    return random.uniform(min_val, max_val) * multiplier


def percentages_remove(lst, tarr, percentage):
    # Calculate the number of items to remove
    num_to_remove = int(len(lst) * percentage)
    arr = lst
    #print(f'Len {len(arr)}')
    if len(lst) > 3:
        start_index = random.randint(2, len(arr) - 2)
    else:
        return lst, tarr
    for _ in range(num_to_remove):
        if len(arr) > 2:  # Make sure there's more than one element to avoid removing the last
            arr.pop(start_index)
            tarr.pop(start_index)
            # Update start index to ensure we don't loop out of range
            start_index = (start_index - 1) % (len(arr) - 1)
    return arr, tarr


def density_remove(arr, density):
    return [arr[i] for i in [0, *range(density - 1, len(arr) - 1, density), len(arr) - 1] if i < len(arr)]


def data_shift(lst, percentage):
    # print(f'Lst {lst}')
    max_shift = 0.00009
    n = int(len(lst) * percentage)
    indices = random.sample(range(2, len(lst) - 2), n)  # Pick indices excluding first (0) and last (-1)
    # print(f'Rand {indices} len {len(lst)}')
    for idx in indices:
        lat = random.uniform(-max_shift, max_shift)
        lon = random.uniform(-max_shift, max_shift)
        lst[idx] = Point(lst[idx].x + lon, lst[idx].y + lat)
    return lst


def shift_percentage(transport, multiplier):
    pt = ['trolleybus', 'bus', 'light rail', 'train']
    transport_limits = {
        "passenger": 0.2,
        "bicycle": 0.12,
        "motorcycle": 0.16
    }
    max_percentage = 0.16 if transport in pt else transport_limits.get(transport, 0.08)
    return random.uniform(0, max_percentage * multiplier)

'''
def convertPTtoWKT(dbname, csvname, basetime, stepjump=1, geoformat='WKT', carslist=[]):
    con = openDB(dbname)
    cur = con.cursor()
    sql_cmd = ('SELECT v.id, datetime, lat, lon, co2 '
               'FROM vehicle_data AS v '
               'WHERE v.id LIKE "%pt%" '
               'ORDER BY v.id, datetime')
    if len(carslist) > 0:
        clist = '\',\''.join(carslist)
        clist = '\'' + clist + '\''
        whereclause = ' AND v.id IN (' + clist + ')'
        sql_cmd += whereclause
    res = cur.execute(sql_cmd)
    coordinate = res.fetchone()
    with open(csvname, 'w') as csvfile:
        csvfile.write(f'id,nr,startstep,starttime,endstep,endtime,wkt\n')
        stepctr = 0  # for each trip/stay (per person) the steps 1,2,3,...
        ctr = 0
        nr = 0
        stop = 0
        id_prev = coordinate[0]
        simulationstep_prev = coordinate[1]
        startsimulationstep = simulationstep_prev
        point_prev = Point(coordinate[3], coordinate[2])
        lat_prev = coordinate[3]
        stop_end = None
        coordinates = []
        timearr =[]
        while coordinate:
            ctr += 1
            stepctr += 1
            if ctr % 5000 == 0:
                print(ctr)
            id = coordinate[0]
            simulationstep = coordinate[1]
            point = Point(coordinate[3], coordinate[2])
            lat = coordinate[3]
            if lat_prev == lat and id == id_prev:
                stop += 1
            elif stop >= 50 and lat != lat_prev and id == id_prev:
                stop_end = True
            else:
                stop = 0
            if id != id_prev or stop_end or simulationstep - simulationstep_prev > 1 :
                nr += 1

                if stop_end:
                    if simulationstep_prev - stop != startsimulationstep:
                        trip = coordinates[:-stop]
                        wktstr, length = coordinates2WKT(trip, geoformat)

                        simulationstep_prev -= stop + 1
                        starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                        endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                        csvstr = f'"{id_prev}","{nr}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{enddate}","{wktstr}"\n'
                        csvfile.write(csvstr)
                        startsimulationstep = simulationstep_prev + 1
                        simulationstep_prev = simulationstep - 1
                        nr += 1
                    stop_end = False
                    stop = 0
                    wktstr, length = coordinates2WKT([point_prev], geoformat)
                else:
                    wktstr, length = coordinates2WKT(coordinates, geoformat)
                stepctr = 0
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                csvstr = f'"{id_prev}","{nr}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{enddate}","{wktstr}"\n'
                csvfile.write(csvstr)
                coordinates = []
                timearr = []
                timearr.append(simulationstep)
                coordinates.append(point)
                if stop >= 600:
                    startsimulationstep = simulationstep_prev
                else:
                    startsimulationstep = simulationstep
                if id != id_prev:
                    nr = 0
            else:
                if stepctr % stepjump == 0:
                    coordinates.append(point)
                    timearr.append(simulationstep)
            id_prev = id
            point_prev = point
            simulationstep_prev = simulationstep
            lat_prev = lat
            coordinate = res.fetchone()
        if stop >= 600:
            if simulationstep_prev - stop != startsimulationstep:
                trip = coordinates[:-stop]
                wktstr, length = coordinates2WKT(trip, geoformat)
                simulationstep_prev -= stop + 1
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                csvstr = f'"{id_prev}","{nr}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{enddate}","{wktstr}"\n'
                csvfile.write(csvstr)
                startsimulationstep = simulationstep_prev + 1
                simulationstep_prev = simulationstep - 1
                nr += 1
            wktstr, length = coordinates2WKT([point_prev], geoformat)
        else:
            wktstr, length = coordinates2WKT(coordinates, geoformat)
        starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
        endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
        csvstr = f'"{id_prev}","{nr}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{enddate}","{wktstr}"\n'
        csvfile.write(csvstr)
    con.close()
    print(ctr)
    print('finished')
'''

def convertSQLtoWKTraw(dbinname, csvname, basetime, eraser, shift, error, density=1, stepjump=1, geoformat='WKT', personlist=[]):
    # open database to read
    con = openDB(dbinname)
    cur = con.cursor()  # to read data
    cur2 = con.cursor()
    # get curser to simulated coordinates
    sql_cmd = ("SELECT   p.name, v.name AS transport, datetime, lat, lon, speed "
               "FROM pedestrian_data AS p, vehicles AS v "
               f"WHERE transport = v.id and lat != 'inf'")  # and MOD(p.datetime, {density}) = {res}
    sql_cmd2 = ('Select pi.id, pt.Type as Occupation '
                'From personal_Info As pi '
                'Join people_type As pt On pt.id = pi.type_id')
    if len(personlist) > 0:
        plist = '\',\''.join(personlist)
        plist = '\'' + plist + '\''
        whereclause = ' AND p.name IN (' + plist + ')'
        sql_cmd += whereclause
    sql_cmd += " ORDER BY p.name, datetime"
    print(sql_cmd)
    res = cur.execute(sql_cmd)
    res2 = cur2.execute(sql_cmd2)
    info = res2.fetchone()
    # print(f"RES: \n{info}")
    coordinate = res.fetchone()
    # open csvfile
    with open(csvname, "w") as csvfile:
        # write heading
        csvfile.write(
            "id,userid,type,mode,geometry,length,timearray,started_at_date,started_at_time,finished_at_date,finished_at_time,confirmed\n")
        # loop through all simulated coordinates
        stepctr = 0  # for each trip/stay (per person) the steps 1,2,3,...
        ctr = 0
        # store first data line as previous data
        name_prev = coordinate[0]
        transport_prev = coordinate[1]  # string such as "on foot", "bus", ...
        simulationstep_prev = coordinate[2]  # min is 1
        startsimulationstep = simulationstep_prev
        point_prev = Point(coordinate[4], coordinate[3])  # shapely object
        lat_prev = coordinate[4]
        stop_end = None  # variable for end of stop
        if error:
            print(f'Errors will be added')
        else:
            print(f'Simulation Data will be saved without adding errors')
        transport_trip_prev = transport_prev
        coordinates = []  # list of all points of a trip/stay'
        timearr = []  # list of time for every point
        nr = 0  # consecutive number of trip/stay of one person
        stop = 0  # counter for stop time
        erase_prob = eraser_percentages(info[1], eraser)
        mob_list = ["T", "S", "Ps", "Bs"]  # trip and stay
        inf = 0
        while coordinate:
            ctr += 1
            stepctr += 1
            # print out some progress information
            if ctr % 5000 == 0:
                print(ctr)
            # Read current data and check for end of trip or stay
            name = coordinate[0]
            transport = coordinate[1]
            simulationstep = coordinate[2]
            lat = coordinate[4]
            point = Point(coordinate[4], coordinate[3])  # shapely object
            # Getting a stop with time more than 600 sec
            if lat == lat_prev and name == name_prev and lat_prev != 'inf' and transport_prev == transport:
                stop += 1
            elif stop >= 600 and lat != lat_prev:
                stop_end = True
                print(f"Stop for {name_prev} at {simulationstep_prev} for {stop}")
            else:
                stop = 0

            # End trip if
            # a) user name changes
            # b) transport mode changes
            # c) there is a stop with time > 600 (not implemented yet)
            # d) there is an unreasonable jump in position > 100m (not implemented yet)
            if name != name_prev or stop_end or transport_prev != transport or simulationstep - simulationstep_prev > density:

                nr += 1
                if stop_end:
                    if transport_prev != transport_trip_prev or transport_prev == transport_trip_prev or transport_prev != transport:
                        if simulationstep_prev - stop != startsimulationstep:
                            # write first trip before stay if stay is 1 activity
                            mobtype = mob_list[0]
                            # getting trip data without stay
                            # print(f"Name {name_prev}   unterschied {simulationstep_prev - stop}  {startsimulationstep}")
                            trip = coordinates[:-stop]
                            triptime = timearr[:-stop]
                            trip = density_remove(trip, density)
                            triptime = density_remove(triptime, density)
                            if error:
                                trip, triptime = percentages_remove(trip, triptime, erase_prob)
                                percent = shift_percentage(transport_prev, shift)
                                trip = data_shift(trip, percent)
                            wktstr, length = coordinates2WKT(trip, geoformat)
                            # adjusting time for trip
                            simulationstep_prev -= stop + 1
                            starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                            endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                            csvstr = f'"{nr}","{name_prev}","{mobtype}","{transport_prev}","{wktstr}","{length}","{triptime}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                            csvfile.write(csvstr)
                            startsimulationstep = simulationstep_prev + 1
                            if name != name_prev:
                                simulationstep_prev += stop + 1
                            else:
                                simulationstep_prev = simulationstep - 1
                            nr += 1
                    mobtype = mob_list[1]
                    # definition of point where stay is
                    stop_end = False
                    timearr = timearr[-stop:]
                    timearr = density_remove(timearr, density)
                    stop = 0
                    wktstr, length = coordinates2WKT([point_prev], geoformat)
                else:
                    mobtype = mob_list[0]
                    coordinates = density_remove(coordinates, density)
                    timearr = density_remove(timearr, density)
                    if error:
                        # print(f'Len {len(coordinates)}  ?? {len(timearr)}')
                        coordinates, timearr = percentages_remove(coordinates, timearr, erase_prob)
                        percent = shift_percentage(transport_prev, shift)
                        coordinates = data_shift(coordinates, percent)
                    wktstr, length = coordinates2WKT(coordinates, geoformat)

                # Add coordinate as the last one if not coordinate of next user
                # if name == name_prev:
                #    coordinates.append(point)
                stepctr = 0
                # Convert time objects into time strings
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                if mobtype == mob_list[0]:
                    mode = transport_prev
                else:
                    mode = ''
                # NO SPACE AFTER COMMA!
                # print(f'Timearr {timearr}')
                csvstr = f'"{nr}","{name_prev}","{mobtype}","{mode}","{wktstr}","{length}","{timearr}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                csvfile.write(csvstr)
                if mobtype == mob_list[3]:
                    journey += 1
                coordinates = []  # start new trip
                timearr = []
                transport_trip_prev = transport_prev
                coordinates.append(point)
                timearr.append(simulationstep)
                if stop >= 600:
                    startsimulationstep = simulationstep_prev
                else:
                    startsimulationstep = simulationstep
                # If change of user store current coordinate and reset trip/stay number and change
                # transport for previous trip
                if name != name_prev:
                    journey = 1
                    transport_trip_prev = transport
                    info = res2.fetchone()
                    if info[0] != name:
                        print(f"????")
                    erase_prob = eraser_percentages(info[1], eraser)
            else:
                # consider only every stepjump time the current point
                # print(f'check {stepctr} {stepjump}')
                if stepctr % stepjump == 0:
                    coordinates.append(point)
                    timearr.append(simulationstep)
            name_prev = name
            transport_prev = transport
            simulationstep_prev = simulationstep
            point_prev = point
            lat_prev = lat
            coordinate = res.fetchone()
        # end of loop, write last trip to file
        if stop >= 600:
            print(f"Stop for {name_prev} at time {startsimulationstep} for {simulationstep_prev - stop}")
            if simulationstep_prev - stop != startsimulationstep:
                nr += 1
                mobtype = mob_list[0]
                # Getting trip data without stay
                trip = coordinates[:-stop]
                triptime = timearr[:-stop]
                trip = density_remove(trip, density)
                triptime = density_remove(triptime, density)
                if error:
                    trip, triptime = percentages_remove(trip, triptime, erase_prob)
                    percent = shift_percentage(transport_prev, shift)
                    trip = data_shift(trip, percent)
                wktstr, length = coordinates2WKT(trip, geoformat)

                # Adjusting time for trip
                simulationstep_prev -= stop
                starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
                csvstr = f'"{nr}","{name_prev}","{mobtype}","{transport_prev}","{wktstr}","{length}","{triptime}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
                csvfile.write(csvstr)
                startsimulationstep = simulationstep_prev
                simulationstep_prev = simulationstep
            mobtype = mob_list[1]
            timearr = timearr[-stop:]
            timearr = density_remove(timearr, density)
            wktstr, length = coordinates2WKT([point_prev], geoformat)
        else:
            mobtype = mob_list[0]
            coordinates = density_remove(coordinates, density)
            timearr = density_remove(timearr, density)
            if error:
                # print(f'Len {len(coordinates)}  ?? {len(timearr)}')
                coordinates, timearr = percentages_remove(coordinates, timearr, erase_prob)
                percent = shift_percentage(transport_prev, shift)
                coordinates = data_shift(coordinates, percent)
            wktstr, length = coordinates2WKT(coordinates, geoformat)

        starttime, startdate = simulationstep2datetimestr(basetime, startsimulationstep)
        endtime, enddate = simulationstep2datetimestr(basetime, simulationstep_prev)
        nr += 1
        # NO SPACE AFTER COMMA!
        csvstr = f'"{nr}","{name_prev}","{mobtype}","{transport_prev}","{wktstr}","{length}","{timearr}","{startdate}","{starttime}","{enddate}","{endtime}","0"\n'
        if mobtype == mob_list[3]:
            journey += 1
        csvfile.write(csvstr)
    con.close()
    print(ctr)
    print("finished")


# dump the data of a simulation SQLITE3 db into csv
def dumpdb2csv(dbname, csvname, personlist=[]):
    # open database to read
    con = openDB(dbname)
    cur = con.cursor()  # to read data
    # get curser to simulated coordinates
    sql_cmd = """
                SELECT * 
                FROM pedestrian_data
            """
    if len(personlist) > 0:
        plist = '\',\''.join(personlist)
        plist = '\'' + plist + '\''
        whereclause = 'WHERE name IN (' + plist + ')'
        sql_cmd += whereclause
        print(sql_cmd)
    res = cur.execute(sql_cmd)
    coordinate = res.fetchone()
    # open csvfile
    with open(csvname, "w") as csvfile:
        # write heading
        # pedestrian_data (name VARCHAR (5) NOT NULL, transport INTEGER NOT NULL REFERENCES vehicles (id), datetime INTEGER NOT NULL, lat DOUBLE NOT NULL, lon DOUBLE NOT NULL, speed DOUBLE NOT NULL);
        csvfile.write("name,transport,datetime,lat,lon,speed\n")
        # loop through coordinates
        ctr = 0
        while coordinate:
            ctr += 1
            if ctr % 5000 == 0:
                print(ctr)
            name = coordinate[0]
            transport = coordinate[1]
            datetime = coordinate[2]
            lat = coordinate[3]
            lon = coordinate[4]
            speed = coordinate[5]
            # NO SPACE AFTER COMMA!
            csvstr = f'{name},{transport},{datetime},{lat},{lon},{speed}\n'
            csvfile.write(csvstr)
            coordinate = res.fetchone()
    con.close()
    print(ctr)
    print("finished")


def main():
    # stepjump = n only takes ever n-th point, reduces size
    # geoformat = 'WKB' is 13% smaller than 'WKT', however WKB might fail in Kepler.gl
    # csv file with raw points in WKT is 93% smaller than db file
    args = parse_args()
    db = args.d
    output_file = args.o
    eraser = args.e
    shift = args.s
    error = args.err
    raw = args.raw
    density = args.den
    print(db + ".db")
    if raw:
        convertSQLtoWKTraw(db + ".db", output_file + ".csv", "2024-04-01 08:00:00", eraser, shift, error, density)
        print(f'Motiontag Format was chosen')
    else:
        convertSQLtoWKT(db + ".db", output_file + ".csv", "2024-04-01 08:00:00", eraser, shift, error, density)
        print(f'Our Format was chosen')


if __name__ == "__main__":
    main()