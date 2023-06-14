import os, sys
import traci
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pytz
import datetime
def getdatetime(): #function to get current date in Germany
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    currentDT = utc_now.astimezone(pytz.timezone("Europe/Berlin"))
    DATETIME = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    return DATETIME
class Human: #creating a human class for retrieving information
    def __init__(self, name, start_edge, destination_edge,line,mode, vType,depart):
        self.name = name #getting variables from input
        self.start_edge = start_edge
        self.destination_edge = destination_edge
        self.line=line
        self.mode=mode
        self.vType=vType
        self.home=self.start_edge[0]
        self.depart=depart
    def __str__(self): # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Destination edge: {self.destination_edge}"
    def go_to_work(self): #creating a function that creates trip and adds person
        line = traci.lane.getIDList()
        traci.person.add(self.name, self.start_edge[0],0.5, depart=0.0)
        traci.person.appendDrivingStage(self.name,self.destination_edge,line)
        self.start_edge,self.destination_edge=self.destination_edge,self.start_edge
class Worker(Human): #creating a subclass of Human
    def __init__(self, name, start_edge, destination_edge,line,mode, vType,depart):
        super().__init__(name, start_edge, destination_edge,line,mode, vType,depart) #getting variables from class human
        self.work=self.destination_edge[0] #getting variables that are different from Human
        self.salary=random.randrange(3300,4800)
        self.age=random.randrange(30,60)
    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Work: {self.work}\n Destination edge: {self.destination_edge}"
class Student(Human): #creating a second subclass of Human
    def __init__(self, name, start_edge, destination_edge,line,mode, vType,depart):
        super().__init__(name, start_edge, destination_edge,line,mode, vType,depart)#getting variables from class human
        self.uni=self.destination_edge[0] #getting variables that are different from Human
        self.scholarship=random.randrange(800,1100)
        self.age=random.randrange(20,30)
    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Uni: {self.uni}\n Destination edge: {self.destination_edge}"
class Pupil(Human): #creating a second subclass of Human
    def __init__(self, name, start_edge, destination_edge,line,mode, vType,depart):
        super().__init__(name, start_edge, destination_edge,line,mode, vType,depart)#getting variables from class human
        self.school=self.destination_edge[0]#getting variables that are different from Human
        self.pocket_money=random.randrange(40,100)
        self.age=random.randrange(5,20)
    def __str__(self):  # method of output of information
        return f"Passenger name: {self.name}\nStart edge: {self.start_edge}\n Home: {self.home}\n Uni: {self.uni}\n Destination edge: {self.destination_edge}"
class Senior(Human):
    def __init__(self,name,start_edge,destination_edge,line,mode,vType,depart):
        super().__init__(name,start_edge,destination_edge,line,mode,vType,depart)#getting variables from class human
        self.pension=random.randrange(2000,4000) #getting variables that are different from Human
        self.age=random.randrange(60,100)
class Homeless(Human):
    def __init__(self,name,start_edge,destination_edge,line,mode,vType, depart):
        super().__init__(name,start_edge,destination_edge,line,mode,vType,depart)
        self.allowance=random.randrange(400,500)
        self.age=random.randrange(30,70)
if 'SUMO_HOME' in os.environ: #checking the environment for SUMO
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
sumoCmd = ["sumo-gui", "-c", "Final\\osm.sumocfg"]  #saving directory of the file
traci.start(sumoCmd)  #starting simulation
tree=ET.parse('Final\\osm_car.rou.xml') #retrieving information about created passengers from xml file
root=tree.getroot()
#Creating an empty root element to hold the data:
root_person = ET.Element("Persons")
root_trip = ET.Element("Trips")
root_vehicle=ET.Element("Vehicles")
persons = [] #creating a list for all existing persons in a file
quantaty_people=1
for person_elem in root.iter("person"): #saving information in class
    id = person_elem.get("id") #creating new variables to save informations
    depart = float(person_elem.get("depart"))
    personTrips = [] #creating new lists
    start_edges=[]
    destination_edges=[]
    lines=[]
    modes=[]
    vTypes=[]
    # Iterate over the 'personTrip' elements within 'person'
    for personTrip_elem in person_elem.iter("personTrip"):
        from_ = personTrip_elem.get("from")
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
    if quantaty_people<=10:#appending list of persons
        person = Worker(id, start_edges, destination_edges, lines, modes, vTypes, depart)
        persons.append(person)
    elif quantaty_people<=20:
        person = Student(id, start_edges, destination_edges, lines, modes, vTypes, depart)
        persons.append(person)
    elif quantaty_people<=30:
        person=Pupil(id, start_edges, destination_edges, lines, modes, vTypes, depart)
        persons.append(person)
    elif quantaty_people<=40:
        person=Senior(id,start_edges,destination_edges,lines,modes,vTypes,depart)
        persons.append(person)
    else:
        person=Homeless(id,start_edges,destination_edges,lines,modes,vTypes,depart)
        persons.append(person)
    quantaty_people+=1
for person in persons:
    person_element = ET.SubElement(root_person,"Person")  # creating a new XML element and add sub-elements for each data item in perList
    name_element = ET.SubElement(person_element, "Name") # Set attributes for the person element
    name_element.text = person.name #Setting information for XML file
    age_element=ET.SubElement(root_person,'Age')
    age_element.text=str(person.age)
    if isinstance(person,Homeless):
        home_element=ET.SubElement(person_element,'Schelter')
    else:
        home_element=ET.SubElement(person_element,'Home')
    home_element.text=person.home
    if isinstance(person, Student):
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
        school_element=ET.SubElement(person_element,'School')
        school_element.text=person.school
        pocket_money_element=ET.SubElement(person_element,'PocketMoney')
        pocket_money_element.text=str(person.pocket_money)
    elif isinstance(person, Senior):
        pension_element=ET.SubElement(person_element,'Pension')
        pension_element.text=str(person.pension)
    elif isinstance(person, Homeless):
        allowance_element=ET.SubElement(person_element,'Allowance')
        allowance_element.text=str(person.allowance)
    start_element = ET.SubElement(person_element, 'StartEdges')
    start_element.text = str(person.start_edge)
    dest_element = ET.SubElement(person_element, 'DestinationEdges')
    dest_element.text = str(person.destination_edge)
    line_element = ET.SubElement(person_element, 'Lines')
    line_element.text = str(person.line)
    mode_element = ET.SubElement(person_element, 'Modes')
    mode_element.text = str(person.mode)
    vType_element = ET.SubElement(person_element, 'vType')
    vType_element.text = str(person.vType)
    depart_element = ET.SubElement(person_element, 'Depart')
    depart_element.text = str(person.depart)
tree_person = ET.ElementTree(root_person) # Write the persons XML tree to a file
xml_string = ET.tostring(root_person, encoding="utf-8")
dom = minidom.parseString(xml_string)
formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
with open("data_person.xml", "w") as file:
    file.write(formatted_xml)
p1=Human('V',["-692537992","-105914659#1"],"-105914659#1",'1','public','car','0') #trying to make a trip dynamic directly in traci using Class
p1.go_to_work()
k=0
while traci.simulation.getMinExpectedNumber() > 0: #making a step in simulation
    traci.simulationStep()
    for person in persons: # crating a loop to retrieve a information
        step=0
        if person.name in traci.person.getIDList():  # checking is the trip still going
            # Function descriptions
            # https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
            # https://sumo.dlr.de/pydoc/traci._person.html#VehicleDomain-getSpeed
            x, y = traci.person.getPosition(person.name)
            coord = [x, y]
            lon, lat = traci.simulation.convertGeo(x, y)
            gpscoord = [lon, lat]
            spd = round(traci.person.getSpeed(person.name) * 3.6, 2)
            edge = traci.person.getRoadID(person.name)
            lane = traci.person.getLaneID(person.name)
            turnAngle = round(traci.person.getAngle(person.name), 2)  # Packing of all the data for export to CSV/XLSX
            perList = [getdatetime(), person.name, coord, gpscoord, spd, edge, lane, turnAngle]
            per_element = ET.SubElement(root_trip, "Person") #creating a new XML element and add sub-elements for each data item in perList:
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
            if step == 0 and k>person.depart:
                # Trip has ended
                print("Trip for person", person.name, "has ended")
                step += 1
    # Write the trip XML tree to a file
    tree_trip = ET.ElementTree(root_trip)
    xml_string = ET.tostring(root_trip, encoding="utf-8")
    dom = minidom.parseString(xml_string)
    formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
    with open("data_trip.xml", "w") as file:
        file.write(formatted_xml)
    vehicles = traci.vehicle.getIDList()
    for vehicle in vehicles:
        x2, y2 = traci.vehicle.getPosition(vehicle)
        coord2 = [x2, y2]
        lon, lat = traci.simulation.convertGeo(x2, y2)
        gpscoord2 = [lon, lat]
        spd2 = round(traci.vehicle.getSpeed(vehicle) * 3.6, 2)
        edge2 = traci.vehicle.getRoadID(vehicle)
        lane2 = traci.vehicle.getLaneID(vehicle)
        displacement2 = round(traci.vehicle.getDistance(vehicle), 2)
        turnAngle2 = round(traci.vehicle.getAngle(vehicle), 2)
        nextTLS2 = traci.vehicle.getNextTLS(vehicle)
        veh_element=ET.SubElement(root_vehicle,'Vehicle')
        name_element2=ET.SubElement(veh_element,'id')
        name_element2.text=vehicle
        coord_element2=ET.SubElement(veh_element,'Coordinates')
        coord_element2.text=str(coord2)
        gpscoord_element2=ET.SubElement(veh_element,'GpsCoordinates')
        gpscoord_element2.text=str(gpscoord2)
        spd_element2=ET.SubElement(veh_element,'Speed')
        spd_element2.text=str(spd2)
        edge_element2=ET.SubElement(veh_element,'Edge')
        edge_element2.text=str(edge2)
        lane_element2=ET.SubElement(veh_element,'Lane')
        lane_element2.text=lane2
        displacement_element2=ET.SubElement(veh_element,'Displacement')
        displacement_element2.text=str(displacement2)
        turnAngle_element2=ET.SubElement(veh_element,'TurnAngle')
        turnAngle_element2.text=str(turnAngle2)
        nextTLS_element2=ET.SubElement(veh_element,'NextTLS')
        nextTLS_element2.text=str(nextTLS2)
    # Write the trip XML tree to a file
    tree_vehicle = ET.ElementTree(root_vehicle)
    xml_string = ET.tostring(root_vehicle, encoding="utf-8")
    dom = minidom.parseString(xml_string)
    formatted_xml = dom.toprettyxml(indent="  ")  # Save the formatted XML to a file
    with open("data_vehicles.xml", "w") as file:
        file.write(formatted_xml)
    k+=1
traci.close()
