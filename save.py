import os
import sys
import traci
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import csv

if 'SUMO_HOME' in os.environ:  # checking the environment for SUMO
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
sumoCmd1 = ["sumo-gui", "-c", "Retrieve\\osm.sumocfg"]  # saving directory of the file
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
        if random.choice([True, False]):  # choosing random could person have a transport
            if random.choice([True, False]):  # if  yes, then how much
                self.vType = random.sample(Trip.autos, k=random.randint(1, 3))
            else:  # else random choosing a one type
                self.vType = random.choice(Trip.autos)
        else:  # and in last person does not have any possibility's except public transport
            self.vType = None

    @staticmethod
    def get_allowed(edge, allow_auto):  # creating a function that will append lists of allowed lane
        for lane in traci.lane.getIDList():
            if traci.lane.getEdgeID(lane) == edge:
                allow_auto.append(traci.lane.getAllowed(lane))

    @staticmethod
    def create_trips(persons, n):
        """ Creating a function that will take list of created persons and one number for quantity
        of trips for one person. Then saves all it in one xml file for simulation. For one treep is
        needed location and destination, type of transport or mode, but not both.
        """
        root_2 = ET.Element("routes")
        vtypes = [
            {"id": "passenger", "vClass": "passenger"},
            {"id": "bicycle", "vClass": "bicycle"},
            {"id": "motorcycle", "vClass": "motorcycle"}
        ]
        # creating a list that must be at the start of xml file. It is a type of transport for persons. passenger = car
        for vType in vtypes:
            ET.SubElement(root_2, 'vType', attrib=vType)  # saving all transport to xml
        for person in persons:
            # creating and saving person in xml file depart - time of start. File must be sorted by departure time
            person_attrib = {'id': person.name, 'depart': '0.00'}
            person_element = ET.SubElement(root_2, 'person', attrib=person_attrib)
            c = 0
            location = person.home  # setting a start position for everyone as Home
            while c <= n:  # creating a loop that will choose destination that`s different from location
                rd = random.choice(person.destination)
                while rd == location:  # creating another loop to make sure that destination`s different
                    rd = random.choice(person.destination)
                person.assign_trip(location, rd)  # using function to add trip for a person
                location = rd  # setting new location for person
                c += 1
            for trip in person.trip:  # now we`re working with trips
                if trip.vType is not None:
                    allowed_auto = []  # creating a list of allowed transport on a start point
                    Trip.get_allowed(trip.start_edge, allowed_auto,)
                    if type(trip.vType) is list:  # checking if person have more than one type of transport
                        random_auto = random.choice(trip.vType)  # choosing random from given list
                    else:  # else using only one transport that is possible
                        random_auto = trip.vType

                    # if our auto is not allowed on a start point
                    if not any(random_auto in group for group in allowed_auto):
                        #  getting a route by which person will travel
                        next_edges = traci.simulation.findIntermodalRoute(trip.start_edge, trip.destination_edge,
                                                                          vType=random_auto)
                        if next_edges:
                            allowed_a = []  # creating a new list of allowed autos on next edge
                            for edge in next_edges[0].edges:  # making a loop to find the closest suitable edge
                                Trip.get_allowed(edge, allowed_a)
                                if any(random_auto in group for group in allowed_a):
                                    next_e = edge
                                    break
                                else:
                                    allowed_a = []
                            # creating trip attribute from start to suitable edge using public transport
                            trip_attrib = {
                                'from': trip.start_edge, 'to': next_e,
                                'line': trip.line, 'modes': trip.mode}
                            ET.SubElement(person_element, 'personTrip', attrib=trip_attrib)  # saving trip attribute
                            # and then from suitable edge to destination
                            trip_attrib = {
                                'from': next_e, 'to': trip.destination_edge,
                                'line': trip.line, 'vTypes': random_auto}  # creating trip attribute for xml file
                        else:
                            trip_attrib = {
                                'from': trip.start_edge, 'to': trip.destination_edge,
                                'line': trip.line, 'vTypes': random_auto}
                    else:  # if  edge is suitable from the start creating only one trip
                        trip_attrib = {
                            'from': trip.start_edge, 'to': trip.destination_edge,
                            'line': trip.line, 'vTypes': random_auto}
                else:  # and if person does not have any transport he`ll use public transport
                    trip_attrib = {
                        'from': trip.start_edge, 'to': trip.destination_edge,
                        'line': trip.line, 'modes': trip.mode}
                if trip.destination_edge == person.supermarket:  # getting a duration that depends on location
                    duration = random.randint(600, 1200)
                elif trip.destination_edge == person.friends:
                    duration = random.randint(3600, 14400)
                elif isinstance(person, Worker) and trip.destination_edge == person.work:
                    # checking instance because not everyone have this attribute
                    duration = random.randint(28800, 36000)
                elif isinstance(person, Student) and trip.destination_edge == person.uni:
                    duration = random.randint(10800, 21600)
                elif isinstance(person, Pupil) and trip.destination_edge == person.school:
                    duration = random.randint(14400, 21600)
                elif isinstance(person, Senior) and trip.destination_edge == person.park:
                    duration = random.randint(1800, 7200)
                else:
                    duration = random.randint(42000, 43200)
                ET.SubElement(person_element, 'personTrip', attrib=trip_attrib)  # saving trip attribute
                stop_attrib = {'duration': str(duration), 'actType': 'singing'}  # creating stop attribute
                ET.SubElement(person_element, 'stop', attrib=stop_attrib)  # saving stop attribute
        xml_2string = ET.tostring(root_2, encoding="utf-8")  # using normal encoding for xml file
        dom = minidom.parseString(xml_2string)  # this two lines help to create readable xml file
        formatted_xml = dom.toprettyxml(indent="  ")
        with open("Without_transport/data.rou.xml", "w") as save:  # Writing information that we`ve saved to the xml fil
            save.write(formatted_xml)

    @staticmethod
    def pedestrian_retrieval(persons, data_list):
        # function will retrieve information of a person movement in every simulation step
        for person in persons:  # creating a loop to retrieve an information about persons
            if person.name in traci.person.getIDList():  # checking is the trip still going
                # Function descriptions
                # https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
                # https://sumo.dlr.de/pydoc/traci._person.html#VehicleDomain-getSpeed
                data_list.append(person.name)
                if traci.person.getVehicle(person.name):
                    data_list.append(traci.person.getVehicle(person.name))
                else:
                    data_list.append("Public")
                data_list.append(traci.simulation.getTime())
                x, y = traci.person.getPosition(person.name)  # getting position of person
                coord = [x, y]  # making a list of positions
                data_list.append(str(coord))
                lon, lat = traci.simulation.convertGeo(x, y)  # converting position to geo
                gpscoord = [lon, lat]  # saving gps to a list
                data_list.append(str(gpscoord))
                spd = round(traci.person.getSpeed(person.name) * 3.6, 2)  # getting speed in km/h
                data_list.append(str(spd))
                edge = traci.person.getRoadID(person.name)  # getting edge
                data_list.append(str(edge))
                lane = traci.person.getLaneID(person.name)  # getting lane
                data_list.append(str(lane))
                turnangle = round(traci.person.getAngle(person.name),
                                  2)  # Packing of all the data for export to CSV/XLSX
                data_list.append(str(turnangle))
        """# Write the trip XML tree to a file
        # Next line helps to make a structure of XML file readable
        xml_string = ET.tostring(root, encoding="utf-8")
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
        with open("data_trip.xml", "w") as save:  # Writing information that we`ve saved to the xml file
            save.write(formatted_xml)"""

    @staticmethod
    def autos_retrieval(autos, root):
        # function will retrieve information about vehicles in every simulation step
        for vehicle in autos:  # creating a loop to retrieve information about vehicles
            x, y = traci.vehicle.getPosition(vehicle)  # getting their position
            coord = [x, y]  # getting their coordinates
            lon, lat = traci.simulation.convertGeo(x, y)  # converting them to geo
            gpscoord = [lon, lat]  # saving them into a list
            spd = round(traci.vehicle.getSpeed(vehicle) * 3.6, 2)  # getting a km/h speed of vehicle
            edge = traci.vehicle.getRoadID(vehicle)  # getting edge
            lane = traci.vehicle.getLaneID(vehicle)  # getting line
            displacement = round(traci.vehicle.getDistance(vehicle), 2)  # getting distance
            turnangle = round(traci.vehicle.getAngle(vehicle), 2)  # getting turn angle
            nexttls = traci.vehicle.getNextTLS(vehicle)  # getting next TLS
            veh_element = ET.SubElement(root, 'Vehicle')  # creating all SubElements and saving a current values
            name_element = ET.SubElement(veh_element, 'id')  # getting and saving name of a vehicle
            name_element.text = vehicle
            datetime_element = ET.SubElement(veh_element, "DateTime")  # getting and saving simulation time
            datetime_element.text = traci.simulation.getTime()
            coord_element = ET.SubElement(veh_element, 'Coordinates')  # getting and saving coordinates of a vehicle
            coord_element.text = str(coord)
            gpscoord_element = ET.SubElement(veh_element, 'GpsCoordinates')  # getting  vehicles gps coordinates
            gpscoord_element.text = str(gpscoord)  # saving vehicles gps coordinates
            spd_element = ET.SubElement(veh_element, 'Speed')  # getting and saving speed of a vehicle
            spd_element.text = str(spd)
            edge_element = ET.SubElement(veh_element, 'Edge')  # getting and saving edge of a vehicle
            edge_element.text = str(edge)
            lane_element = ET.SubElement(veh_element, 'Lane')  # getting and saving lane of a vehicle
            lane_element.text = lane
            displacement_element = ET.SubElement(veh_element, 'Displacement')  # getting and saving vehicle displacement
            displacement_element.text = str(displacement)
            turnangle_element = ET.SubElement(veh_element, 'TurnAngle')  # getting and saving turn angle of a vehicle
            turnangle_element.text = str(turnangle)
            nexttls_element = ET.SubElement(veh_element, 'NextTLS')  # getting and saving TLS of a vehicle
            nexttls_element.text = str(nexttls)

    @staticmethod
    def xml_save(root, filename):
        xml_string = ET.tostring(root, encoding="utf-8")  # next lines helping to make xml more readable
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")
        with open(filename, "w") as save:  # saving information to xml file
            save.write(formatted_xml)

    @staticmethod
    def csv_save(filename, data_list1, data_list2):
        with open(filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data_list1)  # Write Header
            writer.writerows(data_list2)  # Write data


class Human:  # creating a human class for retrieving information
    """ Creating a class Human to create persons. Human will have some global points for trips
    that will be suitable for all subclasses for example House and supermarket. Also, every
    Human will have their own list of trips. List of destination is places where person can go in simulation
    """
    edges = traci.edge.getIDList()  # getting edges from simulation
    filtered_edges = [edge for edge in edges if '_' not in edge]  # sorted edges

    def __init__(self, name):

        self.name = name  # getting variables from input
        self.trip = []
        self.home = random.choice(Human.filtered_edges)
        self.supermarket = random.choice(Human.filtered_edges)
        self.friends = random.choice(Human.filtered_edges)
        self.destination = [self.home, self.supermarket, self.friends]
        self.age = random.randint(0, 99)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        self.trip.append(Trip(start_edge, destination_edge))

    @staticmethod
    def save_humans(persons):
        """ Static method, that will save personal data like Name, salary, pocket money, house address etc. in
        xml file. Using for this given list of people that was created earlier.
        """
        root_person = ET.Element("Persons")
        for person in persons:  # iterating list person, to save information about people in new file
            # creating a new XML element and add sub-elements for each data item in perList
            person_element = ET.SubElement(root_person, "Person")
            name_element = ET.SubElement(person_element, "Name")  # Set attributes for the person element
            name_element.text = person.name  # Setting information for XML file
            age_element = ET.SubElement(root_person, 'Age')  # Creating age element
            age_element.text = str(person.age)  # saving age element
            home_element = ET.SubElement(person_element, 'Home')  # creating house element
            home_element.text = person.home  # save house element
            friend_element = ET.SubElement(person_element, 'Friend')  # creating and saving a friends house
            friend_element.text = person.friends
            if isinstance(person, Student):
                # creating check statements so that people`ll get their own elements that are different for everyone
                uni_element = ET.SubElement(person_element, 'Uni')  # getting and saving uni for person
                uni_element.text = person.uni
                scholarship_element = ET.SubElement(person_element, 'Scholarship')  # getting and saving scholarship
                scholarship_element.text = str(person.scholarship)
            elif isinstance(person, Worker):
                work_element = ET.SubElement(person_element, 'Work')  # getting and saving work for person
                work_element.text = person.work
                salary_element = ET.SubElement(person_element, 'Salary')  # getting and saving salary for person
                salary_element.text = str(person.salary)
            elif isinstance(person, Pupil):
                school_element = ET.SubElement(person_element, 'School')  # getting and saving school for person
                school_element.text = person.school
                pocket_money_element = ET.SubElement(person_element, 'PocketMoney')  # getting and saving pocket money
                pocket_money_element.text = str(person.pocket_money)
            elif isinstance(person, Senior):
                park_element = ET.SubElement(person_element, 'Park')  # getting and saving park for a person
                park_element.text = person.park
                pension_element = ET.SubElement(person_element, 'Pension')  # getting and saving pension for
                pension_element.text = str(person.pension)
            trips_element = ET.SubElement(person_element, "Trips")  # Create trips element
            for trip in person.trip:
                start_element = ET.SubElement(trips_element, "Start_Edge")  # getting and saving start_edge element
                start_element.text = str(trip.start_edge)
                dest_element = ET.SubElement(trips_element, 'Destination_Edge')  # getting and saving dest_edge element
                dest_element.text = str(trip.destination_edge)
                line_element = ET.SubElement(trips_element, 'Line')  # getting and saving line element
                line_element.text = str(trip.line)
                if trip.mode is not None:
                    # getting and saving mode for person if he`s using public transport
                    mode_element = ET.SubElement(trips_element, 'Mode')
                    mode_element.text = str(trip.mode)
                else:
                    # getting and saving vehicle for person if he`s using vehicle
                    vtype_element = ET.SubElement(trips_element, 'vType')
                    vtype_element.text = str(trip.vType)
        xml_string = ET.tostring(root_person, encoding="utf-8")  # next lines helping to make xml more readable
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")
        with open("data_person.xml", "w") as save:  # saving information to xml file
            save.write(formatted_xml)


class Worker(Human):  # creating a subclass of Human
    """
    Subclass of Human. Only difference in personal information like age etc. And also worker is having more
    places to go for example work.
    """
    def __init__(self, name):
        super().__init__(name, )  # getting variables from class human
        self.salary = random.randrange(3300, 4800)  # getting a random salary in range
        self.age = random.randrange(30, 60)  # getting a random age in range
        self.work = random.choice(Human.filtered_edges)
        self.destination.append(self.work)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)


class Student(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Student is having more
        places to go for example uni.
    """
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.uni = None  # getting variables that are different from Human
        self.scholarship = random.randrange(800, 1100)  # getting random scholarship in range
        self.age = random.randrange(20, 30)  # getting random age in range
        self.uni = random.choice(Human.filtered_edges)
        self.destination.append(self.uni)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)


class Pupil(Human):  # creating a second subclass of Human
    """
        Subclass of Human. Only difference in personal information like age etc. And also Pupil is having more
        places to go for example school.
    """
    def __init__(self, name):
        super().__init__(name, )  # getting variables from class human
        self.school = random.choice(Human.filtered_edges)  # getting variables that are different from Human
        self.pocket_money = random.randrange(40, 100)  # getting random pocket money in range
        self.age = random.randrange(5, 20)  # getting random age in range
        self.destination.append(self.school)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)


class Senior(Human):  # creating a subclass of Human
    """
         Subclass of Human. Only difference in personal information like age etc. And also Senior is having more
         places to go for example park.
     """
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.park = None  # getting variables that are different from Human
        self.pension = random.randrange(2000, 4000)  # getting random pension in range
        self.age = random.randrange(60, 100)  # getting random age in range
        self.park = random.choice(Human.filtered_edges)
        self.destination.append(self.park)

    def assign_trip(self, start_edge, destination_edge):  # Function will create trips with first class Trip
        super().assign_trip(start_edge, destination_edge)


humans = []  # creating an empty list for person that`ll be created
for i in range(5):  # creating 12 people with different type of class
    if i < 3:
        human = Worker(f'p{i}')  # creating a Worker
    elif i < 6:
        human = Student(f'p{i}')  # creating a Student
    elif i < 9:
        human = Pupil(f'p{i}')  # creating a Senior
    else:
        human = Senior(f'p{i}')  # creating a Senior
    humans.append(human)
Trip.create_trips(humans, 1)  # using a function to create 5 trips for every person
Human.save_humans(humans)
sumoCmd2 = ["sumo-gui", "-c", "Without_transport\\osm.sumocfg"]  # saving directory of the 2nd file
traci.start(sumoCmd2, label='sim2')  # starting second simulation
traci.switch('sim1')  # switching back to first simulation
traci.close()  # ending first simulation
traci.switch('sim2')  # switching back to second simulation
vehicles = traci.vehicle.getIDList()  # getting list of vehicles id`s
root_vehicle = ET.Element("Vehicles")
root_trips = ET.Element("Trips")  # creating main element Trips for
pedestrian_data = []
vehicles_data = []
pedestrian_header = ["Name", "Transport", "Coord", "Gpscoord", "Speed", "Edge", "Lane", "Turn Angle"]
while traci.simulation.getMinExpectedNumber() > 0:  # making a step in simulation while there`re still some trips
    traci.simulationStep()  # making one step
    Trip.pedestrian_retrieval(humans, pedestrian_data)  # using static function to retrieve pedestrian data every step
    print(pedestrian_data)
    Trip.autos_retrieval(vehicles, root_vehicle)  # using static function to retrieve vehicle data every step
Trip.csv_save('data_trip.csv', pedestrian_header, pedestrian_data)  # saving a data about trips a
Trip.xml_save(root_vehicle, 'data_vehicles.xml')  # saving data about vehicles
traci.close()  # closing a simulation
vehicles_header = []
# Code was used to create tables in db file
"""
        for vehicle in autos:  # creating a loop to retrieve information about vehicles
            x, y = traci.vehicle.getPosition(vehicle)  # getting their position
            coord = [x, y]  # getting their coordinates
            lon, lat = traci.simulation.convertGeo(x, y)  # converting them to geo
            gpscoord = [lon, lat]  # saving them into a list
            spd = round(traci.vehicle.getSpeed(vehicle) * 3.6, 2)  # getting a km/h speed of vehicle
            edge = traci.vehicle.getRoadID(vehicle)  # getting edge
            lane = traci.vehicle.getLaneID(vehicle)  # getting line
            displacement = round(traci.vehicle.getDistance(vehicle), 2)  # getting distance
            turnangle = round(traci.vehicle.getAngle(vehicle), 2)  # getting turn angle
            # Executing an SQL query, which will insert new data into vehicle_data table
            connection.execute(''' INSERT INTO vehicle_data (id, datetime, coordinates, gpscoordinates, 
                            speed, edge, lane, displacement, turnangle) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (vehicle, str(traci.simulation.getTime()),
                                                                       str(coord), str(gpscoord), spd, str(edge),
                                                                       str(lane), str(turnangle), str(displacement),
                                                                       )) """
"""
        for person in persons:  # creating a loop to retrieve an information about persons
            if person.name in traci.person.getIDList():  # checking is the trip still going
                # Function descriptions
                # https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
                # https://sumo.dlr.de/pydoc/traci._person.html#VehicleDomain-getSpeed
                x, y = traci.person.getPosition(person.name)  # getting position of person
                coord = [x, y]  # making a list of positions
                spd = round(traci.person.getSpeed(person.name) * 3.6, 2)  # getting speed in km/h
                lane = traci.person.getLaneID(person.name)  # getting lane
                vehicle = traci.person.getVehicle(person.name)
                if vehicle:
                    vehicletype = traci.vehicle.getVehicleClass(vehicle)
                    if vehicletype == 'bus':  # checking type of transport
                        transport = 1
                    elif vehicletype == 'trolleybus':
                        transport = 2
                    elif vehicletype == 'light rail':
                        transport = 3
                    elif vehicletype == 'train':
                        transport = 4
                    elif vehicletype == 'bicycle':
                        transport = 5
                    elif vehicletype == 'motorcycle':
                        transport = 6
                    elif vehicletype == 'passenger':
                        transport = 7
                else:
                    transport = 8  # if there`s no transport then person is going by foot
                # Executing an SQL query, which will insert new data into vehicle_data table
                connection.execute(''' INSERT INTO pedestrian_data (name, transport, datetime, coord, 
                speed, lane) VALUES (?, ?, ?, ?, ?, ?)''',
                                   (person.name, transport, traci.simulation.getTime(), str(coord),
                                    spd, lane))"""
"""
# Create a table to store pedestrian data
conn.execute('''CREATE TABLE IF NOT EXISTS pedestrian_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    coord TEXT NOT NULL,
                    gpscoord TEXT NOT NULL,
                    speed TEXT NOT NULL,
                    edge TEXT NOT NULL,
                    lane TEXT NOT NULL,
                    turnangle TEXT NOT NULL
                    )''')
# Create a table to store vehicle data
conn.execute('''CREATE TABLE IF NOT EXISTS vehicle_data (
                    id TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    coordinates TEXT NOT NULL,
                    gpscoordinates TEXT NOT NULL,
                    speed TEXT NOT NULL,
                    edge TEXT NOT NULL,
                    lane TEXT NOT NULL,
                    displacement TEXT NOT NULL,
                    turnangle TEXT NOT NULL,
                    nexttls TEXT NOT NULL
                    )''')
"""
"""veh_element = ET.SubElement(root, 'Vehicle')  # creating all SubElements and saving a current values
            name_element = ET.SubElement(veh_element, 'id')  # getting and saving name of a vehicle
            name_element.text = vehicle
            datetime_element = ET.SubElement(veh_element, "DateTime")  # getting and saving simulation time
            datetime_element.text = traci.simulation.getTime()
            coord_element = ET.SubElement(veh_element, 'Coordinates')  # getting and saving coordinates of a vehicle
            coord_element.text = str(coord)
            gpscoord_element = ET.SubElement(veh_element, 'GpsCoordinates')  # getting  vehicles gps coordinates
            gpscoord_element.text = str(gpscoord)  # saving vehicles gps coordinates
            spd_element = ET.SubElement(veh_element, 'Speed')  # getting and saving speed of a vehicle
            spd_element.text = str(spd)
            edge_element = ET.SubElement(veh_element, 'Edge')  # getting and saving edge of a vehicle
            edge_element.text = str(edge)
            lane_element = ET.SubElement(veh_element, 'Lane')  # getting and saving lane of a vehicle
            lane_element.text = lane
            displacement_element = ET.SubElement(veh_element, 'Displacement')  # getting and saving vehicle displacement
            displacement_element.text = str(displacement)
            turnangle_element = ET.SubElement(veh_element, 'TurnAngle')  # getting and saving turn angle of a vehicle
            turnangle_element.text = str(turnangle)
            nexttls_element = ET.SubElement(veh_element, 'NextTLS')  # getting and saving TLS of a vehicle
            nexttls_element.text = str(nexttls)
            """

"""per_element = ET.SubElement(root, "Person")
       # creating a new XML element and add sub-elements for each data item:
       name_element = ET.SubElement(per_element, "Name")  # getting and saving persons name
       name_element.text = person.name
       transport_element = ET.SubElement(per_element, 'Transport')  # getting and saving persons transport
       transport_element.text = traci.person.getVehicle(person.name)
       datetime_element = ET.SubElement(per_element, "DateTime")  # getting and saving simulation time
       datetime_element.text = str(traci.simulation.getTime())
       coord_element = ET.SubElement(per_element, "Coord")  # getting and saving persons coordinates
       coord_element.text = str(coord)
       gpscoord_element = ET.SubElement(per_element, "GPSCoord")  # getting and saving persons gps coordinates
       gpscoord_element.text = str(gpscoord)
       spd_element = ET.SubElement(per_element, "Speed")  # getting and saving persons speed
       spd_element.text = str(spd)
       edge_element = ET.SubElement(per_element, "Edge")  # getting and saving persons edge in simulation
       edge_element.text = str(edge)
       lane_element = ET.SubElement(per_element, "Lane")  # getting and saving persons line in simulation
       lane_element.text = str(lane)
       turnangle_element = ET.SubElement(per_element, "TurnAngle")  # getting and saving persons turn angle
       turnangle_element.text = str(turnangle)
# Write the trip XML tree to a file
# Next line helps to make a structure of XML file readable
xml_string = ET.tostring(root, encoding="utf-8")
dom = minidom.parseString(xml_string)
formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
with open("data_trip.xml", "w") as save:  # Writing information that we`ve saved to the xml file
   save.write(formatted_xml)"""
