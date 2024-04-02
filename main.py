import sys
import traci
import random
import platform
import os
from lxml import etree
import sqlite3
from threading import Thread
import pickle

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
sumoCmd1 = ["sumo", "-c", "Without_transport" + slash_char + "osm.sumocfg", "--device.rerouting.threads", "64",
            "-W", "--step-log.period", "2"]  # saving directory of the file
traci.start(sumoCmd1, label='sim1')  # starting simulation


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

    def __init__(self, start_edge, destination_edge):
        self.start_edge = start_edge
        self.destination_edge = destination_edge
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
    def get_allowed(edge, allow_auto):  # creating a function that will append lists of allowed lane
        for lane in traci.lane.getIDList():
            if traci.lane.getEdgeID(lane) == edge:
                allow_auto.add((traci.lane.getAllowed(lane)))

    @staticmethod
    def get_lane(edge):  # creating a function that will convert edge to the lane
        for lane in traci.lane.getIDList():
            if traci.lane.getEdgeID(lane) == edge:
                return lane

    @staticmethod
    def convert_lane_to_gps(lane):  # creating a functuion that will convert edge to lon and lat
        lane_shape = traci.lane.getShape(lane)
        for x, y in lane_shape:
            lon, lat = traci.simulation.convertGeo(x, y)
        return lon, lat

    @staticmethod
    def get_suitable_edge(next_edges, random_auto, allowed_a, count):
        next_edge = next_edges[0].edges[0]
        for edge in next_edges[0].edges:  # making a loop to find the closest suitable edge
            count += 1
            if count % 15 == 0:  # every 15 edges checking for a suitable edge
                Trip.get_allowed(edge, allowed_a)
                if any(random_auto in group for group in allowed_a):
                    next_edge = edge
                    break
                else:
                    allowed_a = set()
                    next_edge = edge
            else:
                next_edge = edge

        return next_edge

    @staticmethod
    def get_duration(person, destination_edge):
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
        else:
            return random.randint(4200, 8400)

    @staticmethod
    def create_trips(persons, n):
        """ Creating a function that will take list of created persons and one number for quantity
        of trips for one person. Then saves all it in one xml file for simulation. For one treep is
        needed location and destination, type of transport or mode, but not both.
        """
        root_2 = etree.Element("routes")
        for person in persons:
            # creating and saving person in xml file depart - time of start. File must be sorted by departure time
            person_attrib = {'id': person.name, 'depart': '0.00'}
            allowed_auto = set()  # creating a list of allowed transport on a start point
            person_element = etree.SubElement(root_2, 'person', attrib=person_attrib)
            for _ in range(n):  # creating a loop that will choose destination that`s different from location
                # Choose a destination different from the current location
                destination = random.choice([d for d in person.destination if d != person.location])
                print(f'Name dest {person.name} From {person.location} to {destination}')
                person.assign_trip(person.location, destination)
                person.location = destination  # Update the person's location
            for trip in person.trip:  # now we`re working with trips
                print(f'Name Start {person.name} From {trip.start_edge} to {trip.destination_edge}')
                if trip.vType:
                    Trip.get_allowed(trip.start_edge, allowed_auto)
                    if isinstance(trip.vType, list):  # checking if person have more than one type of transport
                        random_auto = random.choice(trip.vType)  # choosing random from given list
                    else:  # else using only one transport that is possible
                        random_auto = trip.vType
                    # if our auto is not allowed on a start point
                    if not any(random_auto in group for group in allowed_auto):
                        #  getting a route by which person will travel
                        next_edges = traci.simulation.findIntermodalRoute(trip.start_edge, trip.destination_edge,
                                                                          modes='car public', vType=random_auto)
                        # print(next_edges)
                        if next_edges:
                            allowed_a = set()  # creating a new list of allowed autos on next edge
                            b = 0  # creating variable to count edges
                            next_e = Trip.get_suitable_edge(next_edges, random_auto, allowed_a, b)
                            # creating trip attribute from start to suitable edge using public transport
                            trip_attrib = {
                                'from': trip.start_edge, 'to': next_e,
                                'line': trip.line, 'modes': trip.mode}
                            etree.SubElement(person_element, 'personTrip', attrib=trip_attrib)  # saving trip attribute
                            # and then from suitable edge to destination
                            trip_attrib = {
                                'from': next_e, 'to': trip.destination_edge,
                                'line': trip.line, 'vTypes': random_auto}  # creating trip attribute for xml file
                        else:
                            # print(f'Name Auto1 {person.name} From {trip.start_edge} to {trip.destination_edge}')

                            trip_attrib = {
                                'from': trip.start_edge, 'to': trip.destination_edge,
                                'line': trip.line, 'vTypes': random_auto}
                    else:  # if  edge is suitable from the start creating only one trip
                        # print(f'Name Auto2 {person.name} From {trip.start_edge} to {trip.destination_edge}')

                        trip_attrib = {
                            'from': trip.start_edge, 'to': trip.destination_edge,
                            'line': trip.line, 'vTypes': random_auto}
                else:  # and if person does not have any transport he`ll use public transport
                    # print(f'Name Public {person.name} From {trip.start_edge} to {trip.destination_edge}')
                    trip_attrib = {
                        'from': trip.start_edge, 'to': trip.destination_edge,
                        'line': trip.line, 'modes': trip.mode}
                duration = Trip.get_duration(person, trip.destination_edge)
                etree.SubElement(person_element, 'personTrip', attrib=trip_attrib)  # saving trip attribute
                stop_attrib = {'duration': str(duration), 'actType': 'singing'}  # creating stop attribute
                etree.SubElement(person_element, 'stop', attrib=stop_attrib)  # saving stop attribute
        xml_2string = etree.tostring(root_2, encoding="utf-8")  # using normal encoding for xml file
        dom = etree.fromstring(xml_2string)  # this two lines help to create readable xml file
        formatted_xml = etree.tostring(dom, pretty_print=True, encoding="utf-8").decode()
        with open("Without_transport/data.rou.xml", "w") as save:  # Writing information that we`ve saved to the xml fil
            save.write(formatted_xml)

    @staticmethod
    def pedestrian_retrieval(connection):
        # function will retrieve information of a person movement in every simulation step
        for per_id in traci.person.getIDList():  # using a built-in subscription to get all variables
            traci.person.subscribe(per_id, [traci.constants.VAR_VEHICLE, traci.constants.VAR_POSITION,
                                            traci.constants.VAR_SPEED])
        result = traci.person.getAllSubscriptionResults()  # collecting results into a tuple
        for person, pedestrian_data in result.items():  # saving al information into sql table
            lat, lon = traci.simulation.convertGeo(pedestrian_data[66][0], pedestrian_data[66][1])
            if pedestrian_data[195] == '':  # checking transport type
                transport = 8  # person is going by foot
            else:
                vehicle_type = traci.vehicle.getVehicleClass(pedestrian_data[195])  # getting a vehicle type for ours
                if vehicle_type == 'bus':  # checking type of transport
                    transport = 1
                elif vehicle_type == 'trolleybus':
                    transport = 2
                elif vehicle_type == 'light rail':
                    transport = 3
                elif vehicle_type == 'train':
                    transport = 4
                elif vehicle_type == 'bicycle':
                    transport = 5
                elif vehicle_type == 'motorcycle':
                    transport = 6
                else:  # person is traveling by car
                    transport = 7
            # Executing an SQL query, which will insert new data into vehicle_data table
            connection.execute(''' INSERT INTO pedestrian_data (name, transport, datetime, lat, lon, speed) 
                                                    VALUES (?, ?, ?, ?, ?, ?)''',
                               (person, transport, traci.simulation.getTime(),
                                lat, lon,
                                pedestrian_data[64]))

    @staticmethod
    def autos_retrieval(connection):
        # function will retrieve information about vehicles in every simulation step
        for veh_id in traci.simulation.getDepartedIDList():
            traci.vehicle.subscribe(veh_id,
                                    [traci.constants.VAR_POSITION,
                                     traci.constants.VAR_SPEED])
        result = traci.vehicle.getAllSubscriptionResults()
        for vehicle, vehicle_data in result.items():
            lat, lon = traci.simulation.convertGeo(vehicle_data[66][0], vehicle_data[66][1])
            # Executing an SQL query, which will insert new data into vehicle_data table
            connection.execute(''' INSERT INTO vehicle_data (id, datetime, lat, lon,
                                        speed) 
                                        VALUES (?, ?, ?, ?, ?)''',
                               (vehicle, traci.simulation.getTime(),
                                lat, lon,
                                vehicle_data[64]))

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
    edges = traci.edge.getIDList()  # getting edges from simulation
    railway_routes = traci.route.getIDList()
    railway_routes = [element for element in railway_routes if
                      'pt_light_rail' in element or 'pt_monorail' in element
                      or 'pt_train' in element or 'pt_tram' in element]
    railway_edges = set()
    for route_name in railway_routes:
        edge = traci.route.getEdges(route_name)
        railway_edges.update(edge)
    filtered_edges = []
    # print(railway_edges)
    quantity = 5  # quantity of people that will be in simulation
    for edge in edges:
        if not any(c.isalpha() for c in
                   edge) and '_' not in edge and edge not in railway_edges:
            filtered_edges.append(edge)  # saving filtered edges that don`t contain railway edges
    # print(f"Check: {filtered_edges}")

    # Creating lists of existing places for people
    home = random.sample(filtered_edges, int(quantity / 5))
    supermarket = random.sample(filtered_edges, 10)
    friends = random.sample(filtered_edges, 10)

    def __init__(self, name):
        self.name = name  # getting variables from input
        self.trip = []
        self.home = random.choice(Human.home)
        self.home_lane = Trip.get_lane(self.home)
        self.home_lon, self.home_lat = Trip.convert_lane_to_gps(self.home_lane)
        self.supermarket = random.choice(Human.supermarket)
        self.supermarket_lane = Trip.get_lane(self.supermarket)
        self.supermarket_lon, self.supermarket_lat = Trip.convert_lane_to_gps(self.supermarket_lane)
        self.friends = random.choice(Human.friends)
        self.friends_lane = Trip.get_lane(self.friends)
        self.friends_lon, self.friends_lat = Trip.convert_lane_to_gps(self.friends_lane)
        self.location = self.home
        self.destination = [self.home, self.supermarket, self.friends]
        self.age = random.randint(0, 99)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        self.trip.append(Trip(start_edge, destination_edge))

    def delete_trips(self):
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
        with open(filename, 'wb') as f:
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
    work = random.sample(Human.filtered_edges, 10)

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(3300, 4800)  # getting a random salary in range
        self.age = random.randrange(30, 60)  # getting a random age in range
        self.work = random.choice(Worker.work)
        self.work_lane = Trip.get_lane(self.work)
        self.work_lon, self.work_lat = Trip.convert_lane_to_gps(self.work_lane)
        self.destination.append(self.work)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)

    def delete_trips(self):
        super().delete_trips()


class Student(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Student is having more
        places to go for example uni.
    """
    uni = random.sample(Human.filtered_edges, 10)

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(800, 1100)  # getting random scholarship in range
        self.age = random.randrange(20, 30)  # getting random age in range
        self.uni = random.choice(Human.filtered_edges)
        self.uni_lane = Trip.get_lane(self.uni)
        self.uni_lon, self.uni_lat = Trip.convert_lane_to_gps(self.uni_lane)
        self.destination.append(self.uni)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)

    def delete_trips(self):
        super().delete_trips()


class Pupil(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Pupil is having more
        places to go for example school.
    """
    school = random.sample(Human.filtered_edges, 10)

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.school = random.choice(Human.filtered_edges)  # getting variables that are different from Human
        self.school_lane = Trip.get_lane(self.school)
        self.school_lon, self.school_lat = Trip.convert_lane_to_gps(self.school_lane)
        self.money = random.randrange(40, 100)  # getting random pocket money in range
        self.age = random.randrange(5, 20)  # getting random age in range
        self.destination.append(self.school)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)

    def delete_trips(self):
        super().delete_trips()


class Senior(Human):  # creating a subclass of Human
    """
         Subclass of Human. Only difference in personal information like age etc. And also Senior is having more
         places to go for example park.
     """
    park = random.sample(Human.filtered_edges, 10)

    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.money = random.randrange(2000, 4000)  # getting random pension in range
        self.age = random.randrange(60, 100)  # getting random age in range
        self.park = random.choice(Senior.park)
        self.park_lane = Trip.get_lane(self.park)
        self.park_lon, self.park_lat = Trip.convert_lane_to_gps(self.park_lane)
        self.destination.append(self.park)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)

    def delete_trips(self):
        super().delete_trips()


def main():
    conn = sqlite3.connect('simulation_data.db')  # Connecting to a db file with all data
    # Using Threading making our code to run Functions at the same time
    traci.simulationStep()
    t = Thread(target=Trip.delete_all(conn))  # executing a function to create new persons
    t.start()
    quantity_trips = 3
    save_obj = True  # will the simulation be extended
    if save_obj:
        print('Loading persons')
        humans = Human.load_state('state.pkl')
        for human in humans:
            Human.delete_trips(human)
    else:
        print("Creating persons")
        humans = []  # creating an empty list for person that`ll be created
        t1 = Thread(target=Human.create_humans(humans))
        t1.start()
    t2 = Thread(target=Trip.create_trips(humans, quantity_trips))
    t2.start()
    t3 = Thread(target=Human.save_humans(humans, conn))
    t3.start()
    Human.save_state('state.pkl', humans)
    traci.close()
    traci.start(sumoCmd1, label='sim2')  # starting second simulation
    traci.switch('sim2')

    while traci.simulation.getMinExpectedNumber() > 0:  # making a step in simulation while there`re still some trips
        # Using threads again to make simulation faster
        t4 = Thread(target=Trip.pedestrian_retrieval(conn))
        t4.start()
        t5 = Thread(target=Trip.autos_retrieval(conn))
        t5.start()
        conn.commit()  # saving data to a database
        traci.simulationStep()  # making one step
    conn.close()  # closing a connection to database
    traci.close()  # closing a simulation


if __name__ == "__main__":
    main()
