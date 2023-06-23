import os, sys
import traci
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pytz
import datetime


def getdatetime():  # function to get current date in Germany
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    currentDT = utc_now.astimezone(pytz.timezone("Europe/Berlin"))
    DATETIME = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    return DATETIME


class Trip:
    def __init__(self, start_edge, destination_edge, line, mode, vType, depart):
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
        self.line = line
        self.mode = mode
        self.vType = vType
        self.depart = depart


class Human:  # creating a human class for retrieving information
    edges = traci.edge.getIDList()

    def __init__(self, name):
        self.name = name  # getting variables from input
        self.trip = []
        self.home = None

    def assign_trip(self, start_edge, destination_edge, line, mode, vType, depart):
        self.trip.append(Trip(start_edge, destination_edge, line, mode, vType, depart))
        self.home = start_edge[0]

    def set_info(self):
        for edge in person.edges:
            a = 3+2

    def __str__(self):
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Destination edge: {self.destination_edge}"


class Worker(Human):  # creating a subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.salary = random.randrange(3300, 4800)  # getting a random salary in range
        self.age = random.randrange(30, 60)  # getting a random age in range
        self.work = None

    def assign_trip(self, start_edge, destination_edge, line, mode, vType, depart):
        super().assign_trip(start_edge, destination_edge, line, mode, vType, depart)
        self.work = destination_edge[0]

    def print_trips(self):
        return f'All trips for a person: {self.name}\n {self.trip}'

    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Work: {self.work}\n Destination edge: {self.destination_edge}"


class Student(Human):  # creating a second subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.uni = None  # getting variables that are different from Human
        self.scholarship = random.randrange(800, 1100)  # getting random scholarship in range
        self.age = random.randrange(20, 30)  # getting random age in range

    def assign_trip(self, start_edge, destination_edge, line, mode, vType, depart):
        super().assign_trip(start_edge, destination_edge, line, mode, vType, depart)
        self.uni = destination_edge[0]

    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Uni: {self.uni}\n Destination edge: {self.destination_edge}"


class Pupil(Human):  # creating a second subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.school = None  # getting variables that are different from Human
        self.pocket_money = random.randrange(40, 100)  # getting random pocket money in range
        self.age = random.randrange(5, 20)  # getting random age in range

    def assign_trip(self, start_edge, destination_edge, line, mode, vType, depart):
        super().assign_trip(start_edge, destination_edge, line, mode, vType, depart)
        self.school = destination_edge[0]

    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Uni: {self.school}\n Destination edge: {self.destination_edge}"


class Senior(Human):  # creating a subclass of Human
    def __init__(self, name):
        super().__init__(name)  # getting variables from class human
        self.park = None  # getting variables that are different from Human
        self.pension = random.randrange(2000, 4000)  # getting random pension in range
        self.age = random.randrange(60, 100)  # getting random age in range

    def assign_trip(self, start_edge, destination_edge, line, mode, vType, depart):
        super().assign_trip(start_edge, destination_edge, line, mode, vType, depart)
        self.park = destination_edge[0]


if 'SUMO_HOME' in os.environ:  # checking the environment for SUMO
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
sumoCmd = ["sumo-gui", "-c", "Final\\osm.sumocfg"]  # saving directory of the file
traci.start(sumoCmd)  # starting simulation
tree = ET.parse('Final\\osm_car.rou.xml')  # retrieving information about created passengers from xml file
root = tree.getroot()
# Creating an empty root element to hold the data about Persons, their trips and also about vehicles:
root_person = ET.Element("Persons")
root_trip = ET.Element("Trips")
root_vehicle = ET.Element("Vehicles")
persons = []  # creating a list for all existing persons in a file
quantaty_people = 1  # creating a variable, that`ll help to count people
for person_elem in root.iter("person"):  # saving information in class
    id = person_elem.get("id")  # creating new variables to save information
    depart = float(person_elem.get("depart"))
    personTrips = []  # creating new lists to save information
    start_edges = []
    destination_edges = []
    lines = []
    modes = []
    vTypes = []
    # Iterate over the 'personTrip' elements within 'person'
    for personTrip_elem in person_elem.iter("personTrip"):
        from_ = personTrip_elem.get("from")  # getting variables that was in the file
        to = personTrip_elem.get("to")
        line = personTrip_elem.get("lines")
        mode = personTrip_elem.get("modes")
        vType = personTrip_elem.get("vTypes")
        personTrip = from_, to, lines, mode, vType
        personTrips.append(personTrip)
        start_edges.append(from_)
        destination_edges.append(to)
        lines.append(line)
        modes.append(mode)
        vTypes.append(vType)
    if quantaty_people <= 20:  # appending list of persons to a different classes, that depends on what place was they in the file
        person = Worker(id)
        persons.append(person)
        person.assign_trip(start_edges, destination_edges, lines, modes, vTypes, depart)
    elif quantaty_people <= 40:
        person = Student(id)
        persons.append(person)
        person.assign_trip(start_edges, destination_edges, lines, modes, vTypes, depart)
    elif quantaty_people <= 60:
        person = Pupil(id)
        persons.append(person)
        person.assign_trip(start_edges, destination_edges, lines, modes, vTypes, depart)
    else:
        person = Senior(id)
        persons.append(person)
        person.assign_trip(start_edges, destination_edges, lines, modes, vTypes, depart)
    quantaty_people += 1
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
        depart_element = ET.SubElement(trips_element, 'Depart')
        depart_element.text = str(trip.depart)
tree_person = ET.ElementTree(root_person)
xml_string = ET.tostring(root_person, encoding="utf-8")
dom = minidom.parseString(xml_string)
formatted_xml = dom.toprettyxml(indent="  ")

with open("data_person.xml", "w") as file:
    file.write(formatted_xml)
# p1 = Human('V',["-692537992","-105914659#1"],"-105914659#1",'1','public','car','0')  # trying to make a trip dynamic directly in traci using Class
d = traci.edge.getIDList()
print(d)
k = 0  # creating a variable, that`ll help to check a depart time
while traci.simulation.getMinExpectedNumber() > 0:  # making a step in simulation while there`re still some trips
    traci.simulationStep()  # making one step
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
            turnAngle = round(traci.person.getAngle(person.name), 2)  # Packing of all the data for export to CSV/XLSX
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
            if step == 0 and k > trip.depart:
                # Trip has ended
                print("Trip for person", person.name, "has ended")
                step += 1
    # Write the trip XML tree to a file
    tree_trip = ET.ElementTree(root_trip)  # Write the persons trip XML tree to a file
    xml_string = ET.tostring(root_trip, encoding="utf-8")  # This line helps to make a structure of XML file readable
    dom = minidom.parseString(xml_string)
    formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
    with open("data_trip.xml", "w") as file:  # Writng information that we`ve saved to the xml file
        file.write(formatted_xml)
    vehicles = traci.vehicle.getIDList()  # getting list of vehicles id`s
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
    xml_string = ET.tostring(root_vehicle, encoding="utf-8")  # This line helps to make a structure of XML file readable
    dom = minidom.parseString(xml_string)
    formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
    with open("data_vehicles.xml", "w") as file:  # Writng information that we`ve saved to the xml file
        file.write(formatted_xml)
    k += 1
traci.close()  # closing a simulation
