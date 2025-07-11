import sys
import traci
import random
import platform
import os
from lxml import etree
import math
from threading import Thread
import pickle
import argparse
import osmium as osm
import pandas as pd
from Databases.db import connect_db

print(platform.system())  # printing out our system and then creating new variable for slash character
if platform.system() == "Windows":
    slash_char = "\\"
elif platform.system() == "Linux":
    slash_char = "/"
if 'SUMO_HOME' in os.environ:  # checking the environment for SUMO
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
sumoCmd1 = ["sumo", "-c", "Simulation" + slash_char + "osm.sumocfg", "--device.rerouting.threads", "64",
            "-W", "--step-log.period", "100", "--emission-output", "Simulation_Temp/emissions.xml"]  # saving directory of the file
traci.start(sumoCmd1, label='sim1')  # starting simulation


class NodeHandler(osm.SimpleHandler):
    """ The class helps to read and convert gps data from OSM file to SUMO edges"""
    def __init__(self):
        super().__init__()
        self.edge = []  # Initialize a list to store SUMO edges.

    def node(self, n):
        if n.location.valid():  # Check if the node has valid location data.
            lat, lon = n.location.lat, n.location.lon  # Extract latitude and longitude.
            # Convert GPS coordinates to SUMO edge and append to the list of edges.
            res = traci.simulation.convertRoad(lon, lat, isGeo=True)
            self.edge.append(res[0])


class Trip:
    """  edges represent the road segments or links in a transportation network.
          They define the connections between different nodes
          (junctions or intersections) and determine the routes vehicles can take.
           It`s a little bit similar to coordinates. start_edge is a variable which
           defines a start position of a subject that making a trip.destination_edge
           is a variable which defines an end position of a subject that making a trip.
           line refers to a specific lane within an edge or road segment. Lines are
           used to define the physical divisions or markings within an edge, indicating
           separate lanes for vehicles. modes refer to different types or categories
           of transportation modes that can be simulated within the SUMO framework.
           Modes represent the various ways of transportation available to vehicles or
           travelers in the simulated network.In SUMO (Simulation of Urban MObility),
           vType refers to vehicle types. vType is used to define specific characteristics
           and properties of different types of vehicles in a SUMO simulation. depart is
           used to define a time in simulation when the trip starts """
    autos = ['bicycle', 'motorcycle', 'passenger']  # List of usable transport for a person. Passenger = car

    def __init__(self, start_edge, destination_edge, duration):
        self.start_edge = start_edge
        self.destination_edge = destination_edge
        self.duration = duration
        self.line = 'ANY'
        self.mode = 'public'
        if random.random() < 0.5:  # Randomly determine if the person has a transport
            if random.random() < 0.5:  # Randomly determine if they have multiple types of transport
                self.vType = random.sample(Trip.autos, k=random.randint(1, 3))
            else:
                self.vType = random.choice(Trip.autos)  # Randomly choose one type of transport
        else:
            self.vType = None  # No possibility except public transport

    @staticmethod
    def parse_args():
        # Define argument parser
        parser = argparse.ArgumentParser()
        # Add argument for number of trips (-t) with default value 10
        parser.add_argument('-t', type=int, default=10)
        # Add argument for number of persons (-p) with default value 5
        parser.add_argument('-p', type=int, default=5)
        # Add argument for loading/creating of persons with default value False(creating of persons)
        parser.add_argument('-l', type=bool, default=False)
        # Parse arguments
        return parser.parse_args()

    @staticmethod
    def get_allowed(edge):  # creating a function that will append lists of allowed lane
        res = []
        for i in range(0, 6):
            lane = f'{edge}_{i}'
            try:
                res.append(traci.lane.getAllowed(lane))
            except traci.TraCIException:
                print(f' Lane {lane} doesn`t exist')

        return res

    @staticmethod
    def get_lane(edge):  # creating a function that will convert edge to the lane
        for lane in traci.lane.getIDList():
            if traci.lane.getEdgeID(lane) == edge:
                return lane

    @staticmethod
    def convert_edge_to_gps(edge):  # creating a functuion that will convert edge to lon and lat
        lon, lat = traci.simulation.convert2D(edge, 0, toGeo=True)
        lon_formatted = "{:.5f}".format(lon)
        lat_formatted = "{:.5f}".format(lat)
        return lon_formatted, lat_formatted

    @staticmethod
    def get_suitable_edge(next_edges, random_auto, allowed_a, count):
        next_edge = next_edges[0].edges[0]
        for edge in next_edges[0].edges:  # making a loop to find the closest suitable edge
            count += 1
            if count % 5 == 0:  # every 15 edges checking for a suitable edge
                if edge not in allowed_a:
                    allowed_a[edge] = Trip.get_allowed(edge)
                allowed = allowed_a[edge]
                if any(random_auto in group for group in allowed):
                    next_edge = edge
                    break
                else:
                    next_edge = edge
            else:
                next_edge = edge

        return next_edge

    @staticmethod
    def destination_probability(person, current_hour):
        """
        Calculate the probability of a person's next destination based on the current hour and their type.
        """
        destination_probs = {}  # Initialize destination probabilities dictionary
        # Define destination probabilities based on the person's class and time of day
        if 6 <= current_hour <= 9:  # Morning (going to work/uni/school)
            destination_probs[person.home] = 0.05
            destination_probs[person.friends] = 0.05
            if isinstance(person, Worker):
                destination_probs[person.work] = 0.7
                destination_probs[person.supermarket] = 0.2
            elif isinstance(person, Student):
                destination_probs[person.uni] = 0.75
                destination_probs[person.supermarket] = 0.15
            elif isinstance(person, Pupil):
                destination_probs[person.school] = 0.8
                destination_probs[person.supermarket] = 0.1
            elif isinstance(person, Senior):
                destination_probs[person.park] = 0.3
                destination_probs[person.supermarket] = 0.6
        elif 10 <= current_hour <= 15:  # Noon (friends, work/uni/school)
            destination_probs[person.home] = 0.1
            destination_probs[person.supermarket] = 0.2
            if isinstance(person, Worker):
                destination_probs[person.work] = 0.4
                destination_probs[person.friends] = 0.3
            elif isinstance(person, Student):
                destination_probs[person.uni] = 0.3
                destination_probs[person.friends] = 0.4
            elif isinstance(person, Pupil):
                destination_probs[person.school] = 0.4
                destination_probs[person.friends] = 0.3
            elif isinstance(person, Senior):
                destination_probs[person.park] = 0.5
                destination_probs[person.friends] = 0.4

        else:  # Evening (going back home, friends)
            if isinstance(person, Worker):
                destination_probs[person.home] = 0.6
                destination_probs[person.work] = 0.05
                destination_probs[person.friends] = 0.3
            elif isinstance(person, Student):
                destination_probs[person.home] = 0.6
                destination_probs[person.friends] = 0.3
                destination_probs[person.uni] = 0.05
            elif isinstance(person, Pupil):
                destination_probs[person.home] = 0.7
                destination_probs[person.friends] = 0.2
                destination_probs[person.school] = 0.05
            elif isinstance(person, Senior):
                destination_probs[person.home] = 0.7
                destination_probs[person.friends] = 0.2
                destination_probs[person.park] = 0.05
            destination_probs[person.supermarket] = 0.05
        # Remove current location from the list of possible destinations
        current_location = person.location
        destination_probs.pop(current_location, None)
        # Choose a destination based on probabilities
        destination = random.choices(list(destination_probs.keys()), weights=list(destination_probs.values()))[0]
        if destination == person.supermarket:
            person.supermarket = Human.supermarket['edge'].sample(n=1).to_string(index=False)
        elif destination == person.friends:
            person.friends = Human.friends['edge'].sample(n=1).to_string(index=False)
        elif isinstance(person, Senior) and destination == person.park:
            person.park = Senior.park['edge'].sample(n=1).to_string(index=False)
        return destination

    @staticmethod
    def get_duration(person, destination_edge, time):
        """
        Calculate the duration of stay at a given destination for a person based on their type and destination.
        """
        if destination_edge == person.supermarket:
            return random.randint(600, 2400)
        elif destination_edge == person.friends:
            return random.randint(3600, 14400)
        elif isinstance(person, Worker) and destination_edge == person.work:
            return random.randint(28000, 36000)
        elif isinstance(person, Student) and destination_edge == person.uni:
            return random.randint(15000, 34000)
        elif isinstance(person, Pupil) and destination_edge == person.school:
            return random.randint(14000, 21000)
        elif isinstance(person, Senior) and destination_edge == person.park:
            return random.randint(1800, 7200)
        elif 6 <= time <= 15 and destination_edge == person.home:
            return random.randint(4200, 8400)
        else:
            return random.randint(28800, 50400)

    @staticmethod
    def create_trips(persons, n):
        """ Creating a function that will take list of created persons and one number for quantity
        of trips for one person. Then saves all it in one xml file for simulation. For one treep is
        needed location and destination, type of transport or mode, but not both.
        """
        root_2 = etree.Element("routes")
        # Precompute allowed transports for all starting locations
        allowed_transport_cache = {}
        cr = 0
        for person in persons:
            # creating and saving person in xml file depart - time of start. File must be sorted by departure time
            person_attrib = {'id': person.name, 'depart': '21600.00'}
            person_element = etree.SubElement(root_2, 'person', attrib=person_attrib)
            # seting time to 6 am
            time = 6
            for _ in range(n):  # creating a loop that will choose destination that`s different from location
                # Choose a destination different from the current location
                destination = Trip.destination_probability(person, time)
                duration = Trip.get_duration(person, destination, time)
                time = (time + duration / 3600) % 24  # Keep within 24-hour range
                person.assign_trip(person.location, destination, duration)
                person.location = destination  # Update the person's location
            for trip in person.trip:  # now we`re working with trips
                if cr % 100 == 0:
                    print(f'Trip nr {cr}')
                start_edge, destination_edge, duration = trip.start_edge, trip.destination_edge, trip.duration
                vType = trip.vType
                mode = trip.mode

                # Fetch allowed transport modes from cache
                if start_edge not in allowed_transport_cache:
                    allowed_transport_cache[start_edge] = Trip.get_allowed(start_edge)

                allowed_auto = allowed_transport_cache[start_edge]

                if vType:
                    if isinstance(vType, list):
                        random_auto = random.choice(vType)
                    else:
                        random_auto = vType
                    if not any(random_auto in group for group in allowed_auto):
                        # Find a better edge using SUMO (cache results to avoid multiple calls)
                        next_edges = traci.simulation.findIntermodalRoute(start_edge, destination_edge, modes='car',
                                                                          vType=random_auto)

                        if next_edges:
                            next_e = Trip.get_suitable_edge(next_edges, random_auto, allowed_transport_cache, 0)
                            trip_attrib = {'from': start_edge, 'to': next_e, 'line': trip.line, 'modes': mode}
                            etree.SubElement(person_element, 'personTrip', attrib=trip_attrib)
                            trip_attrib = {'from': next_e, 'to': destination_edge, 'line': trip.line,
                                           'vTypes': random_auto}
                        else:
                            trip_attrib = {'from': start_edge, 'to': destination_edge, 'line': trip.line,
                                           'vTypes': random_auto}
                    else:
                        trip_attrib = {'from': start_edge, 'to': destination_edge, 'line': trip.line,
                                       'vTypes': random_auto}
                else:
                    trip_attrib = {'from': start_edge, 'to': destination_edge, 'line': trip.line, 'modes': mode}

                etree.SubElement(person_element, 'personTrip', attrib=trip_attrib)

                stop_attrib = {'duration': str(duration), 'edge': destination_edge, 'actType': 'singing'}
                etree.SubElement(person_element, 'stop', attrib=stop_attrib)
                cr += 1
                # Write XML once at the end

            formatted_xml = etree.tostring(root_2, pretty_print=True, encoding="utf-8").decode()
            with open("Simulation/data.rou.xml", "w") as save:
                save.write(formatted_xml)
        print(f'Trip creation is finished')
    @staticmethod
    def pedestrian_retrieval(connection):
        # function will retrieve information of a person movement in every simulation step
        persons = traci.person.getIDList()
        step = traci.simulation.getTime()
        if not persons and step > 21601:
            print(f'All of the persons have finished their activities')
            traci.close()
        for per_id in persons:  # using a built-in subscription to get all variables
            traci.person.subscribe(per_id, [traci.constants.VAR_VEHICLE, traci.constants.VAR_POSITION,
                                            traci.constants.VAR_SPEED])
        result = traci.person.getAllSubscriptionResults()  # collecting results into a tuple
        for person, pedestrian_data in result.items():  # saving al information into sql table
            lon, lat = traci.simulation.convertGeo(pedestrian_data[66][0], pedestrian_data[66][1])
            if lon == 'inf':
                continue
            else:
                lon = "{:.5f}".format(lon)
                lat = "{:.5f}".format(lat)

            if pedestrian_data[195] == '':  # checking transport type
                transport = 7  # person is going by foot
            else:
                vehicle_type = traci.vehicle.getVehicleClass(pedestrian_data[195])  # getting a vehicle type for ours
                if vehicle_type == 'bus' or vehicle_type == 'trolleybus':  # checking type of transport
                    transport = 1
                elif vehicle_type == 'light rail':
                    transport = 2
                elif vehicle_type == 'train':
                    transport = 3
                elif vehicle_type == 'bicycle':
                    transport = 4
                elif vehicle_type == 'motorcycle':
                    transport = 5
                else:  # person is traveling by car
                    transport = 6
            # Executing an SQL query, which will insert new data into pedestrian_data table
            connection.execute(''' INSERT INTO pedestrian_data (name, transport, datetime, lat, lon, speed) 
                                                    VALUES (?, ?, ?, ?, ?, ?)''',
                               (person, transport, traci.simulation.getTime(),
                                lat, lon,
                                int(pedestrian_data[64])))

    @staticmethod
    def autos_retrieval(connection):
        # function will retrieve information about vehicles in every simulation step
        for veh_id in traci.simulation.getDepartedIDList():
            traci.vehicle.subscribe(veh_id,
                                    [traci.constants.VAR_POSITION,
                                     traci.constants.VAR_SPEED,traci.constants.VAR_CO2EMISSION])
        result = traci.vehicle.getAllSubscriptionResults()
        for vehicle, vehicle_data in result.items():
            lon, lat = traci.simulation.convertGeo(vehicle_data[66][0], vehicle_data[66][1])
            lon = "{:.5f}".format(lon)
            lat = "{:.5f}".format(lat)
            co2 = "{:.0f}".format(vehicle_data[96])
            # Executing an SQL query, which will insert new data into vehicle_data table
            connection.execute(''' INSERT INTO vehicle_data (id, datetime, lat, lon,
                                        speed, co2) 
                                        VALUES (?, ?, ?, ?, ?, ?)''',
                               (vehicle, traci.simulation.getTime(),
                                lat, lon,
                                int(vehicle_data[64]), co2))

    @staticmethod
    def delete_all(connection):  # function will delete all data from previous simulations
        sql_vehicle = 'DELETE FROM vehicle_data'  # Setting an SQL query
        sql_pedestrian = 'DELETE FROM pedestrian_data'  # Setting an SQL query
        sql_pedestrian2 = 'DELETE FROM personal_Info'  # Setting an SQL query

        cur = connection.cursor()
        cur.execute(sql_vehicle)
        cur.execute(sql_pedestrian2)
        cur.execute(sql_pedestrian)  # Executing previous query`s
        connection.commit()  # committing changes


class Human:  # creating a human class for retrieving information
    """ Creating a class Human to create persons. Human will have some global points for trips
    that will be suitable for all subclasses for example House and supermarket. Also, every
    Human will have their own list of trips. List of destination is places where person can go in simulation
    """
    quantity = 5  # quantity of people that will be in simulation
    friends = pd.read_csv('Simulation' + slash_char + 'friends.csv')
    home = pd.read_csv('Simulation' + slash_char + 'home.csv')
    supermarket = pd.read_csv('Simulation' + slash_char + 'shop.csv')

    def __init__(self, name):
        self.name = name  # getting variables from input
        self.trip = []
        self.home = Human.home['edge'].sample(n=1).to_string(index=False)
        self.home_lon, self.home_lat = Trip.convert_edge_to_gps(self.home)
        self.supermarket = Human.supermarket['edge'].sample(n=1).to_string(index=False)
        self.supermarket_lon, self.supermarket_lat = Trip.convert_edge_to_gps(self.supermarket)
        self.friends = Human.friends['edge'].sample(n=1).to_string(index=False)
        self.friends_lon, self.friends_lat = Trip.convert_edge_to_gps(self.friends)
        self.location = self.home
        self.destination = [self.home, self.supermarket, self.friends]
        self.age = random.randint(0, 99)

    def assign_trip(self, start_edge, destination_edge, duration):  # Function will create trips with first class Trip
        self.trip.append(Trip(start_edge, destination_edge, duration))

    def delete_trips(self):  # Function to delete all trips
        self.trip = []

    @staticmethod
    def create_humans(persons):
        for i in range(Human.quantity):  # creating 1000 people with different type of class
            if i < Human.quantity / 4:
                person = Worker(f'p{i}')  # creating a Worker
            elif i < Human.quantity / 2:
                person = Student(f'p{i}')  # creating a Student
            elif i < 3 * Human.quantity / 4:
                person = Pupil(f'p{i}')  # creating a Pupil
            else:
                person = Senior(f'p{i}')  # creating a Senior
            persons.append(person)


    @staticmethod
    def save_humans(persons, connection):
        """ Static method, that will save personal data like Name, salary, pocket money, house address etc. in
        database file. Using for this given list of people that was created earlier.
        """
        for person in persons:
            # checking which class our person have to give special variables
            if isinstance(person, Worker):
                type_id = 1
                place_lon = person.work_lon
                place_lat = person.work_lat
            elif isinstance(person, Student):
                type_id = 2
                place_lon = person.uni_lon
                place_lat = person.uni_lat
            elif isinstance(person, Pupil):
                type_id = 3
                place_lon = person.school_lon
                place_lat = person.school_lat
            else:  # last one is Senior
                type_id = 4
                place_lon = person.park_lon
                place_lat = person.park_lat
            # Executing an SQL query, which will insert new data into vehicle_data table
            connection.execute('''INSERT INTO personal_Info (id, type_id, age, home_lon, home_lat, friends_lon,
             friends_lat, supermarket_lon, supermarket_lat, place_lon, place_lat, money) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (person.name, type_id, person.age, person.home_lon, person.home_lat, person.friends_lon,
                                person.friends_lat, person.supermarket_lon, person.supermarket_lat, place_lon,
                                place_lat, person.money))

    @staticmethod
    def save_state(filename, data):
        """ Static method, that will save all object information so that previous information could be loaded.
         Using for this given list of people that was created earlier.
                """
        with open(f'Simulation_Temp{filename}.pkl', 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def load_state(filename):
        """ Static method, that will load all object information to extend our simulation
                """
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            return data


class Worker(Human):  # creating a subclass of Human
    """
    Subclass of Human. Only difference in personal information like age etc. And also worker is having more
    places to go for example work.
    """
    work = pd.read_csv('Simulation' + slash_char + 'work.csv')


    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(3300, 4800)  # getting a random salary in range
        self.age = random.randrange(30, 60)  # getting a random age in range
        self.work = Worker.work['edge'].sample(n=1).to_string(index=False)
        self.work_lon, self.work_lat = Trip.convert_edge_to_gps(self.work)
        self.destination.append(self.work)

    def assign_trip(self, start_edge, destination_edge, duration):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge, duration)

    def delete_trips(self):
        super().delete_trips()


class Student(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Student is having more
        places to go for example uni.
    """
    uniGps = []  # List for gps Coord
    uni = []  # List for sumo edges
    uniGps.append([48.74527, 9.32249])  # coord of Flandernstrasse
    uniGps.append([48.73831, 9.31112])  # coord of Stadtmitte
    for lat, lon in uniGps:
        res = traci.simulation.convertRoad(lon, lat, isGeo=True)  # converting gps coordinates to sumo edge
        uni.append(res[0])
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(800, 1100)  # getting random scholarship in range
        self.age = random.randrange(20, 30)  # getting random age in range
        self.uni = random.choice(Student.uni)
        # self.uni = Student.uni[0]
        self.uni_lon, self.uni_lat = Trip.convert_edge_to_gps(self.uni)
        self.destination.append(self.uni)

    def assign_trip(self, start_edge, destination_edge, duration):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge, duration)

    def delete_trips(self):
        super().delete_trips()


class Pupil(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Pupil is having more
        places to go for example school.
    """
    school = pd.read_csv('Simulation' + slash_char + 'school.csv')

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.school = Pupil.school['edge'].sample(n=1).to_string(index=False)  # getting variables that are different from Human
        self.school_lon, self.school_lat = Trip.convert_edge_to_gps(self.school)
        self.money = random.randrange(40, 100)  # getting random pocket money in range
        self.age = random.randrange(5, 20)  # getting random age in range
        self.destination.append(self.school)

    def assign_trip(self, start_edge, destination_edge, duration):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge, duration)

    def delete_trips(self):
        super().delete_trips()


class Senior(Human):  # creating a subclass of Human
    """
         Subclass of Human. Only difference in personal information like age etc. And also Senior is having more
         places to go for example park.
     """
    park = pd.read_csv('Simulation' + slash_char + 'park.csv')

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(2000, 4000)  # getting random pension in range
        self.age = random.randrange(60, 100)  # getting random age in range
        self.park = Senior.park['edge'].sample(n=1).to_string(index=False)
        self.park_lon, self.park_lat = Trip.convert_edge_to_gps(self.park)
        self.destination.append(self.park)

    def assign_trip(self, start_edge, destination_edge, duration):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge, duration)

    def delete_trips(self):
        super().delete_trips()


def main():
    filename = 'simulation_data'
    conn = connect_db(filename)  # Connecting to a db file with all data
    # Using Threading making our code to run Functions at the same time
    t = Thread(target=Trip.delete_all(conn))  # executing a function to create new persons
    t.start()
    # Parse command-line arguments
    args = Trip.parse_args()
    quantity_trips = args.t
    Human.quantity = args.p
    save_obj = args.l
    calculated_value = math.floor(Human.quantity / 5)
    n = max(1, calculated_value)
    Human.home = Human.home.sample(n=n)
    Worker.work = Worker.work.sample(n=n)
    if save_obj:
        print('Loading persons')
        try:
            humans = Human.load_state('Simulation_Temp/state.pkl')
        except FileNotFoundError:
            print('No persons loaded, because the File does not exist')
            quit()
        for human in humans:
            Human.delete_trips(human)
    else:
        print("Creating persons")
        humans = []  # creating an empty list for person that`ll be created
        t1 = Thread(target=Human.create_humans(humans))
        t1.start()
    # t2 = Thread(target=Trip.createTrips(duration, csvName))
    # t2.start()
    t22 = Thread(target=Trip.create_trips(humans, quantity_trips))
    t22.start()
    t3 = Thread(target=Human.save_humans(humans, conn))
    t3.start()
    Human.save_state('state', humans)
    traci.close()
    traci.start(sumoCmd1, label='sim2')  # starting second simulation
    traci.switch('sim2')

    while traci.simulation.getMinExpectedNumber() > 0:  # making a step in simulation while there`re still some trips
        # Using threads again to make simulation faster
        t4 = Thread(target=Trip.autos_retrieval(conn))
        t4.start()
        t5 = Thread(target=Trip.pedestrian_retrieval(conn))
        t5.start()

        conn.commit()  # saving data to a database
        traci.simulationStep()  # making one step
    conn.close()  # closing a connection to database


if __name__ == "__main__":
    main()