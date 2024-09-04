# convert-sqlite2csv.py
# Convert SQLITE-DB file to CSV and SQLITE-DB file with additional information
# and with tracks removed that cannot be properly anonymised (e.g. holidays)
# ATTENTION: Adds data to the original SQLITE-DB!
# Dominik Schoop, 25.02.2024


import sys
import csv
import datetime
import binascii # hexlify
from shapely import wkb, wkt, geometry, Point, LineString, get_coordinates, distance
import sqlite3


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


# Convert simulation step into datetime string starting at a base time
# basetime = string of format dd.mm.yyyy hh:mm:ss
# simulationstep = string of integer, starting at 1
def simulationstep2datetimestr(basetimestr, simulationstepstr):
    timeformat = "%Y-%m-%d %H:%M:%S"
    basetime = datetime.datetime.strptime(basetimestr, timeformat)
    simulationstep = int(simulationstepstr) - 1
    time = basetime + datetime.timedelta(seconds=simulationstep)
    return time.strftime(timeformat)


# Construct from a list of Points a string in WKT or WKB format
def coordinates2WKT(coordinates, geoformat="WKT"):
    wktstr = None
    num = len(coordinates)
    if num > 1:  # coordinates form trajectory
        if num > 2500 and geoformat == 'WKB':
            print("WARNING: Number of coordinates might be too large. It is suggested to change to the WKT format.")
        if geoformat == 'WKT':
            wktstr = LineString(coordinates).wkt
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
    return wktstr


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
def convertSQLtoWKT(dbinname, csvname, basetime, stepjump=1, geoformat='WKT', personlist=[]):
    # open database to read
    con = openDB(dbinname)
    cur = con.cursor()  # to read data
    # get curser to simulated coordinates
    sql_cmd = ("SELECT   p.name, v.name AS transport, datetime, lat, lon, speed "
               "FROM pedestrian_data AS p, vehicles AS v "
               "WHERE transport = v.id")  # AND lat < 100 and lat > -100  was deleted, because no data was in those querries
    if len(personlist) > 0:
        plist = '\',\''.join(personlist)
        plist = '\'' + plist + '\''
        whereclause = ' AND p.name IN (' + plist + ')'
        sql_cmd += whereclause
    sql_cmd += " ORDER BY p.name, datetime"
    print(sql_cmd)
    res = cur.execute(sql_cmd)
    coordinate = res.fetchone()
    # open csvfile
    with open(csvname, "w") as csvfile:
        # write heading
        csvfile.write("name,nr,journey,mobtype,transport,startstep,starttime,endstep,endtime,wkt\n")
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
        transport_trip_prev = transport_prev
        coordinates = []  # list of all points of a trip/stay
        nr = 0  # consecutive number of trip/stay of one person
        stop = 0  # counter for stop time
        mob_list = ["trip", "stay", "pt_stay", "big_stay"]  # trip and stay
        public_transport_list = ["bus", "trolleybus", "light rail", "train"]
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
            elif stop >= 600 and lat != lat_prev and name == name_prev:
                stop_end = True
                print(lat_prev)
                print(f"Stop for {name_prev} at {simulationstep_prev} for {stop}")
            else:
                stop = 0

            # End trip if
            # a) user name changes
            # b) transport mode changes
            # c) there is a stop with time > 600 (not implemented yet)
            # d) there is an unreasonable jump in position > 100m (not implemented yet)
            if name != name_prev or stop_end or transport_prev != transport or simulationstep - simulationstep_prev > 1 or distance(
                    point, point_prev) > 0.001:
                if distance(point, point_prev) > 0.001:
                    print(f'Person {name} jumping about!')
                nr += 1
                if stop_end:
                    # print(f'The stop {name} at a time {simulationstep} with dauer {stop}')
                    """
                    if transport_prev == transport:
                        # When the transport before the stop is the same, so a bit of trip is not written
                        if transport_2prev != transport_prev or simulationstep_prev - simulationstep_2prev > 1 or name_2prev != name_prev or distance(point_prev, point_2prev) > 0.001:
                            coordinates = coordinates_prev[0]
                            # implement deleting  the last row from csv file
                        else:
                            if transport_2prev == transport:
                                coordinates = coordinates[:-stop]
                            else:
                                coordinates = coordinates_prev[:-stop]
                            if name == 'p602':
                                print(f'Stop for {stop}  at {coordinates}')
                            mobtype = mob_list[0]
                            wktstr = coordinates2WKT(coordinates_prev, geoformat)
                            simulationstep_prev -= stop
                            starttime = simulationstep2datetimestr(basetime, simulationstep_prev)
                            endtime = simulationstep2datetimestr(basetime, simulationstep_prev)
                            csvstr = f'"{name_prev}","{nr}","{mobtype}","{transport_prev}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{endtime}","{wktstr}"\n'
                            csvfile.write(csvstr)
                            startsimulationstep = simulationstep_prev
                            simulationstep_prev = simulationstep
                            nr += 1
                    stop_end = False
                    mobtype = mob_list[1]
                    # coordinates = coordinates[:-stop]
                    # startsimulationstep -= stop + 1
                    wktstr = coordinates2WKT([point_prev], geoformat)
                    stop = 0
                    print(f'WKTSRT\n{wktstr}')
                    """

                    if nr == 1 or transport_prev != transport_trip_prev or transport_prev == transport_trip_prev or transport_prev != transport:
                        if simulationstep_prev - stop != startsimulationstep:
                            # write first trip before stay if stay is 1 activity
                            mobtype = mob_list[0]
                            # getting trip data without stay
                            # print(f"Name {name_prev}   unterschied {simulationstep_prev - stop}  {startsimulationstep}")
                            trip = coordinates[:-stop]
                            wktstr = coordinates2WKT(trip, geoformat)
                            # adjusting time for trip
                            simulationstep_prev -= stop + 1
                            starttime = simulationstep2datetimestr(basetime, startsimulationstep)
                            endtime = simulationstep2datetimestr(basetime, simulationstep_prev)
                            csvstr = f'"{name_prev}","{nr}","{journey}","{mobtype}","{transport_prev}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{endtime}","{wktstr}"\n'
                            csvfile.write(csvstr)
                            startsimulationstep = simulationstep_prev + 1
                            simulationstep_prev = simulationstep - 1
                            nr += 1
                    if transport in public_transport_list and transport_prev not in public_transport_list:
                        mobtype = mob_list[2]
                    elif stop <= 3600:
                        mobtype = mob_list[1]
                    else:
                        mobtype = mob_list[3]

                    # definition of point where stay is
                    stop_end = False
                    stop = 0

                    wktstr = coordinates2WKT([point_prev], geoformat)
                else:
                   mobtype = mob_list[0]
                   wktstr = coordinates2WKT(coordinates, geoformat)
                # Add coordinate as the last one if not coordinate of next user
                # if name == name_prev:
                #    coordinates.append(point)
                stepctr = 0
                # Convert time objects into time strings

                starttime = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime = simulationstep2datetimestr(basetime, simulationstep_prev)
                # NO SPACE AFTER COMMA!
                csvstr = f'"{name_prev}","{nr}","{journey}","{mobtype}","{transport_prev}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{endtime}","{wktstr}"\n'
                csvfile.write(csvstr)
                if mobtype == mob_list[3]:
                    journey += 1
                coordinates = []  # start new trip
                transport_trip_prev = transport_prev
                coordinates.append(point)
                if stop >= 600:
                    startsimulationstep = simulationstep_prev
                else:
                    startsimulationstep = simulationstep
                # If change of user store current coordinate and reset trip/stay number and change
                # transport for previous trip
                if name != name_prev:
                    nr = 0
                    journey = 1
                    transport_trip_prev = transport
            else:
                # consider only every stepjump time the current point
                if stepctr % stepjump == 0:
                    coordinates.append(point)
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
                wktstr = coordinates2WKT(trip, geoformat)
                # Adjusting time for trip
                simulationstep_prev -= stop
                starttime = simulationstep2datetimestr(basetime, startsimulationstep)
                endtime = simulationstep2datetimestr(basetime, simulationstep_prev)
                csvstr = f'"{name_prev}","{nr}","{journey}","{mobtype}","{transport_prev}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{endtime}","{wktstr}"\n'
                csvfile.write(csvstr)
                startsimulationstep = simulationstep_prev
                simulationstep_prev = simulationstep
            if stop <= 3600:
                mobtype = mob_list[1]
            else:
                mobtype = mob_list[3]
            wktstr = coordinates2WKT([point_prev], geoformat)
        else:
            mobtype = mob_list[0]
            wktstr = coordinates2WKT(coordinates, geoformat)
        starttime = simulationstep2datetimestr(basetime, startsimulationstep)
        endtime = simulationstep2datetimestr(basetime, simulationstep_prev)
        nr += 1
        # NO SPACE AFTER COMMA!
        csvstr = f'"{name_prev}","{nr}","{journey}","{mobtype}","{transport_prev}","{startsimulationstep}","{starttime}","{simulationstep_prev}","{endtime}","{wktstr}"\n'
        if mobtype == mob_list[3]:
            journey += 1
        csvfile.write(csvstr)
    con.close()
    print(ctr)
    print("finished")


def convertSQLtoWKTraw(dbname, csvname, basetime):
    # open database to read
    con = openDB(dbname)
    cur = con.cursor()  # to read data
    # get curser to simulated coordinates
    sql_cmd = """
                SELECT p.name, v.name AS transport, datetime, lat, lon, speed
                FROM pedestrian_data AS p, vehicles AS v
                WHERE transport = v.id
                ORDER BY p.name, datetime
            """
    res = cur.execute(sql_cmd)
    coordinate = res.fetchone()
    # open csvfile
    with open(csvname, "w") as csvfile:
        # write heading
        csvfile.write("name,step,transport,speed,wkt\n")
        # loop through coordinates
        ctr = 0
        while coordinate:
            ctr += 1
            if ctr % 5000 == 0:
                print(ctr)
            name = coordinate[0]
            transport = coordinate[1]
            simulationstep = coordinate[2]
            wktstr = Point(coordinate[3], coordinate[4]).wkt
            speed = coordinate[5]
            # NO SPACE AFTER COMMA!
            csvstr = f'"{name}","{simulationstep}","{transport}","{speed}","{wktstr}"\n'
            csvfile.write(csvstr)
            coordinate = res.fetchone()
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
    filename = 'simulation_data'
    print(filename + ".db")
    convertSQLtoWKT(filename + ".db", "test.csv", "2024-04-01 08:00:00", stepjump=1)
    # convertSQLtoWKTraw(filename+".db", filename+"raw.csv", "2024-04-01 08:00:00")
    # dumpdb2csv(filename+".db", filename+"_dbraw_p136.csv", personlist=['p136'])


if __name__ == "__main__":
    main()