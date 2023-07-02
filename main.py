import os, sys
import traci
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pytz
import datetime
if 'SUMO_HOME' in os.environ:  # checking the environment for SUMO
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
sumoCmd = ["sumo-gui", "-c", "Final\\osm.sumocfg"]  # saving directory of the file
traci.start(sumoCmd)  # starting simulation


def getdatetime():  # function to get current date in Germany
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    currentDT = utc_now.astimezone(pytz.timezone("Europe/Berlin"))
    DATETIME = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    return DATETIME


class Trip:
    autos = ['bicycle', 'motorcycle', 'passenger']

    def __init__(self, start_edge, destination_edge):
        '''  edges represent the road segments or links in a transportation network.
         They define the connections between different nodes
         (junctions or intersections) and determine the routes vehicles can take.
          It`s a little bit similar to coordinates. start_edge is a variable which
          defines a start position of a subject that making a trip.destination_edge
          is a variable which defines a end position of a subject that making a trip.
          line refers to a specific lane within an edge or road segment. Lines are
          used to define the physical divisions or markings within an edge, indicating
          separate lanes for vehicles. modes refer to different types or categories
          of transportation modes that can be simulated within the SUMO framework.
          Modes represent the various ways of transportation available to vehicles or
          travelers in the simulated network.In SUMO (Simulation of Urban MObility),
          vType refers to vehicle types. vType is used to define specific characteristics
          and properties of different types of vehicles in a SUMO simulation. depart is
          used to define a time in simulation when the trip starts'''
        self.start_edge = start_edge
        self.destination_edge = destination_edge
        self.line = 'ANY'
        self.mode = 'public'
        if random.choice([True, False]):
            if random.choice([True, False]):
                self.vType = random.sample(Trip.autos, k=random.randint(1, 3))
            else:
                self.vType = random.choice(Trip.autos)
        else:
            self.vType = None

    @staticmethod
    def create_trips(humans, n):
        root_2 = ET.Element("routes")
        vTypes = [
            {"id": "passenger", "vClass": "passenger"},
            {"id": "bicycle", "vClass": "bicycle"},
            {"id": "motorcycle", "vClass": "motorcycle"}
        ]
        for vType in vTypes:
            ET.SubElement(root_2, 'vType', attrib=vType)
        for human in humans:
            person_attrib = {'id': human.name, 'depart': '0.00'}
            person = ET.SubElement(root_2, 'person', attrib=person_attrib)
            c = 0
            location = human.home
            while c <= n:
                rd = random.choice(human.destination)
                while rd == location:
                    rd = random.choice(human.destination)
                human.assign_trip(location, rd)
                location = rd
                c += 1
            for trip in human.trip:
                allowed_auto = []
                suitable_lanes = []
                if trip.vType is not None:
                    for lane in traci.lane.getIDList():
                        if traci.lane.getEdgeID(lane) == trip.start_edge:
                            suitable_lanes.append(lane)
                            allowed_auto.append(traci.lane.getAllowed(lane))
                    if type(trip.vType) is list:
                        random_auto = random.choice(trip.vType)
                        trip_attrib = {
                            'from': trip.start_edge, 'to': trip.destination_edge,
                            'line': trip.line, 'vTypes': random_auto}
                    else:
                        trip_attrib = {
                            'from': trip.start_edge, 'to': trip.destination_edge,
                            'line': trip.line, 'vTypes': trip.vType}
                else:
                    trip_attrib = {
                        'from': trip.start_edge, 'to': trip.destination_edge,
                        'line': trip.line, 'modes': trip.mode}
                if trip.destination_edge == human.supermarket:
                    duration = random.randint(600, 1200)
                elif isinstance(Human, Worker) and trip.destination_edge == human.work:
                    duration = random.randint(28800, 36000)
                elif trip.destination_edge == human.home:
                    duration = random.randint(42000, 43200)
                ET.SubElement(person, 'personTrip', attrib=trip_attrib)
                stop_attrib = {'duration': str(duration), 'actType': 'singing'}
                ET.SubElement(person, 'stop', attrib=stop_attrib)
        tree_2 = ET.ElementTree(root_2)
        xml_2string = ET.tostring(root_2, encoding="utf-8")
        dom = minidom.parseString(xml_2string)
        formatted_xml = dom.toprettyxml(indent="  ")
        with open("data.xml", "w") as file:  # Writng information that we`ve saved to the xml file
            file.write(formatted_xml)

    @staticmethod
    def pedestrian_retrieval(persons):
        root_trip = ET.Element("Trips")
        for person in persons:  # creating a loop to retrieve a information about persons
            step = 0  # creating a variable that`ll help to know when`ve ended a trip for person
            if person.name in traci.person.getIDList():  # checking is the trip still going
                # Function descriptions
                # https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
                # https://sumo.dlr.de/pydoc/traci._person.html#VehicleDomain-getSpeed
                x, y = traci.person.getPosition(person.name)  # getting position of person
                coord = [x, y]  # making a list of positions
                lon, lat = traci.simulation.convertGeo(x, y)  # converting position to geo
                gpscoord = [lon, lat]  # saving gps to a list
                spd = round(traci.person.getSpeed(person.name) * 3.6, 2)  # getting speed in km/h
                edge = traci.person.getRoadID(person.name)  # getting edge
                lane = traci.person.getLaneID(person.name)  # getting lane
                turnAngle = round(traci.person.getAngle(person.name),
                                  2)  # Packing of all the data for export to CSV/XLSX
                per_element = ET.SubElement(root_trip,
                                            "Person")  # creating a new XML element and add sub-elements for each data item:
                datetime_element = ET.SubElement(per_element, "DateTime")
                datetime_element.text = getdatetime()
                name_element = ET.SubElement(per_element, "Name")
                name_element.text = person.name
                coord_element = ET.SubElement(per_element, "Coord")
                coord_element.text = str(coord)
                gpscoord_element = ET.SubElement(per_element, "GPSCoord")
                gpscoord_element.text = str(gpscoord)
                spd_element = ET.SubElement(per_element, "Speed")
                spd_element.text = str(spd)
                edge_element = ET.SubElement(per_element, "Edge")
                edge_element.text = edge
                lane_element = ET.SubElement(per_element, "Lane")
                lane_element.text = lane
                turnAngle_element = ET.SubElement(per_element, "TurnAngle")
                turnAngle_element.text = str(turnAngle)
            else:
                if step == 0:
                    # Trip has ended
                    print("Trip for person", person.name, "has ended")
                    step += 1
            # Write the trip XML tree to a file
        tree_trip = ET.ElementTree(root_trip)  # Write the persons trip XML tree to a file
        xml_string = ET.tostring(root_trip,
                                 encoding="utf-8")  # This line helps to make a structure of XML file readable
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
        with open("data_trip.xml", "w") as file:  # Writng information that we`ve saved to the xml file
            file.write(formatted_xml)

    @staticmethod
    def autos_retrieval(vehicles):
        root_vehicle = ET.Element("Vehicles")
        for vehicle in vehicles:  # creating a loop to retrieve information about vehicles
            x2, y2 = traci.vehicle.getPosition(vehicle)  # getting their position
            coord2 = [x2, y2]  # getting their coordinates
            lon, lat = traci.simulation.convertGeo(x2, y2)  # converting them to geo
            gpscoord2 = [lon, lat]  # saving them into a list
            spd2 = round(traci.vehicle.getSpeed(vehicle) * 3.6, 2)  # getting a km/h speed of vehicle
            edge2 = traci.vehicle.getRoadID(vehicle)  # getting edge
            lane2 = traci.vehicle.getLaneID(vehicle)  # getting line
            displacement2 = round(traci.vehicle.getDistance(vehicle), 2)  # geting distance
            turnAngle2 = round(traci.vehicle.getAngle(vehicle), 2)  # getting turn angle
            nextTLS2 = traci.vehicle.getNextTLS(vehicle)  # getting next TLS
            veh_element = ET.SubElement(root_vehicle, 'Vehicle')  # creating all SubElements and saving a current values
            name_element2 = ET.SubElement(veh_element, 'id')
            name_element2.text = vehicle
            coord_element2 = ET.SubElement(veh_element, 'Coordinates')
            coord_element2.text = str(coord2)
            gpscoord_element2 = ET.SubElement(veh_element, 'GpsCoordinates')
            gpscoord_element2.text = str(gpscoord2)
            spd_element2 = ET.SubElement(veh_element, 'Speed')
            spd_element2.text = str(spd2)
            edge_element2 = ET.SubElement(veh_element, 'Edge')
            edge_element2.text = str(edge2)
            lane_element2 = ET.SubElement(veh_element, 'Lane')
            lane_element2.text = lane2
            displacement_element2 = ET.SubElement(veh_element, 'Displacement')
            displacement_element2.text = str(displacement2)
            turnAngle_element2 = ET.SubElement(veh_element, 'TurnAngle')
            turnAngle_element2.text = str(turnAngle2)
            nextTLS_element2 = ET.SubElement(veh_element, 'NextTLS')
            nextTLS_element2.text = str(nextTLS2)
        # Write the trip XML tree to a file
        tree_vehicle = ET.ElementTree(root_vehicle)  # Write the vehicles XML tree to a file
        xml_string = ET.tostring(root_vehicle,
                                 encoding="utf-8")  # This line helps to make a structure of XML file readable
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
        with open("data_vehicles.xml", "w") as file:  # Writng information that we`ve saved to the xml file
            file.write(formatted_xml)


class Human:  # creating a human class for retrieving information
    edges = traci.edge.getIDList()
    filtered_edges = [edge for edge in edges if '_' not in edge and not edge.endswith("_0")]

    def __init__(self, name):
        self.name = name  # getting variables from input
        self.trip = []
        self.home = random.choice(Human.filtered_edges)
        self.supermarket = random.choice(Human.filtered_edges)
        self.destination = [self.home, self.supermarket]
        self.age = random.randrange(30, 60)  # getting a random age in range

    def assign_trip(self, start_edge, destination_edge):
        self.trip.append(Trip(start_edge, destination_edge))

    @staticmethod
    def save_humans(persons):
        root_person = ET.Element("Persons")
        for person in persons:  # iterating list person, to save information about people in new file
            person_element = ET.SubElement(root_person,
                                           "Person")  # creating a new XML element and add sub-elements for each data item in perList
            name_element = ET.SubElement(person_element, "Name")  # Set attributes for the person element
            name_element.text = person.name  # Setting information for XML file
            age_element = ET.SubElement(root_person, 'Age')
            age_element.text = str(person.age)
            home_element = ET.SubElement(person_element, 'Home')
            home_element.text = person.home
            if isinstance(person,
                          Student):  # depends on class creating money that people`ll get monthly and also most importante places for this type of people
                uni_element = ET.SubElement(person_element, 'Uni')
                uni_element.text = person.uni
                scholarship_element = ET.SubElement(person_element, 'Scholarship')
                scholarship_element.text = str(person.scholarship)
            elif isinstance(person, Worker):
                work_element = ET.SubElement(person_element, 'Work')
                work_element.text = person.work
                salary_element = ET.SubElement(person_element, 'Salary')
                salary_element.text = str(person.salary)
            elif isinstance(person, Pupil):
                school_element = ET.SubElement(person_element, 'School')
                school_element.text = person.school
                pocket_money_element = ET.SubElement(person_element, 'PocketMoney')
                pocket_money_element.text = str(person.pocket_money)
            elif isinstance(person, Senior):
                pension_element = ET.SubElement(person_element, 'Pension')
                pension_element.text = str(person.pension)
            trips_element = ET.SubElement(person_element, "Trips")  # Create trips element
            for trip in person.trip:
                start_element = ET.SubElement(trips_element, "StartEdge")  # Create start_edge element
                start_element.text = str(trip.start_edge)
                dest_element = ET.SubElement(trips_element, 'DestEdge')
                dest_element.text = str(trip.destination_edge)
                line_element = ET.SubElement(trips_element, 'Line')
                line_element.text = str(trip.line)
                mode_element = ET.SubElement(trips_element, 'Mode')
                mode_element.text = str(trip.mode)
                vType_element = ET.SubElement(trips_element, 'vType')
                vType_element.text = str(trip.vType)
        tree_person = ET.ElementTree(root_person)
        xml_string = ET.tostring(root_person, encoding="utf-8")
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")
        with open("data_person.xml", "w") as file:
            file.write(formatted_xml)


class Worker(Human):  # creating a subclass of Human

    def __init__(self, name):
        super().__init__(name,)  # getting variables from class human
        self.salary = random.randrange(3300, 4800)  # getting a random salary in range
        self.age = random.randrange(30, 60)  # getting a random age in range
        self.work = random.choice(Human.filtered_edges)
        self.destination = [self.home, self.work, self.supermarket]

    def assign_trip(self, start_edge, destination_edge):
        super().assign_trip(start_edge, destination_edge)


class Student(Human):  # creating a second subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.uni = None  # getting variables that are different from Human
        self.scholarship = random.randrange(800, 1100)  # getting random scholarship in range
        self.age = random.randrange(20, 30)  # getting random age in range
        self.uni = random.choice(Human.filtered_edges)

    def assign_trip(self, start_edge, destination_edge):
        super().assign_trip(start_edge, destination_edge)


class Pupil(Human):  # creating a second subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.school = None  # getting variables that are different from Human
        self.pocket_money = random.randrange(40, 100)  # getting random pocket money in range
        self.age = random.randrange(5, 20)  # getting random age in range
        self.school = random.choice(Human.filtered_edges)

    def assign_trip(self, start_edge, destination_edge):
        super().assign_trip(start_edge, destination_edge)


class Senior(Human):  # creating a subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.park = None  # getting variables that are different from Human
        self.pension = random.randrange(2000, 4000)  # getting random pension in range
        self.age = random.randrange(60, 100)  # getting random age in range
        self.park = random.choice(Human.filtered_edges)

    def assign_trip(self, start_edge, destination_edge):
        super().assign_trip(start_edge, destination_edge)


humans = []
with open('names.txt', 'r') as file:
    names = [name.strip() for name in file.readlines()]
random.shuffle(names)
for i in range(5):
    if i < 1:
        human = Human(names[i])
    else:
        human = Worker(names[i])
    humans.append(human)
Trip.create_trips(humans, 2)
Human.save_humans(humans)
vehicles = traci.vehicle.getIDList()  # getting list of vehicles id`s
while traci.simulation.getMinExpectedNumber() > 0:  # making a step in simulation while there`re still some trips
    traci.simulationStep()  # making one step
    Trip.pedestrian_retrieval(humans)
    Trip.autos_retrieval(vehicles)

traci.close()  # closing a simulation
