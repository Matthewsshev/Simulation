import osmium as osm
import traci
import platform
import os
import sys
import argparse

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
            "-W", "--step-log.period", "100"]  # saving directory of the file
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

    @staticmethod
    def parse_args():
        # Define argument parser
        parser = argparse.ArgumentParser()
        # Add argument for all  placement for our trip with default value Without_transport/friends.osm
        parser.add_argument('-f', type=str, default='Without_transport' + slash_char + 'friends.osm')
        # Add argument for number of persons (-p) with default value 1
        parser.add_argument('-s', type=str, default='Without_transport' + slash_char + 'shop.osm')
        parser.add_argument('-home', type=str, default='Without_transport' + slash_char + 'home.osm')
        parser.add_argument('-w', type=str, default='Without_transport' + slash_char + 'work.osm')
        parser.add_argument('-sc', type=str, default='Without_transport' + slash_char + 'school.osm')
        parser.add_argument('-p', type=str, default='Without_transport/park.osm')

        # Parse arguments
        return parser.parse_args()

    @staticmethod
    def save_csv(filename, edge_list):
        filtered_edge = []
        for place in edge_list:
            if not any(c.isalpha() for c in place) and '_' not in place:
                filtered_edge.append(place)
        with open(filename, 'w') as save:
            save.write(f'edge\n')
            for place in filtered_edge:
                save.write(f'{place}\n')


# Parse command-line arguments
args = NodeHandler.parse_args()
# Define paths to OSM files for different locations
osm_file = args.f
osm_file1 = args.s
osm_file2 = args.home
osm_file3 = args.w
osm_file4 = args.sc
osm_file5 = args.p
# Create NodeHandler instances for handling OSM data
handler_Friends = NodeHandler()
handler_Supermarket = NodeHandler()
handler_Home = NodeHandler()
handler_Work = NodeHandler()
handler_School = NodeHandler()
handler_Park = NodeHandler()
handler_Stop = NodeHandler()
# Apply OSM files to NodeHandlers to extract location data
handler_Friends.apply_file(osm_file)
handler_Supermarket.apply_file(osm_file1)
handler_Home.apply_file(osm_file2)
handler_Work.apply_file(osm_file3)
handler_School.apply_file(osm_file4)
handler_Park.apply_file(osm_file5)
edge_friends = handler_Friends.edge
edge_supermarket = handler_Supermarket.edge
edge_home = handler_Home.edge
edge_work = handler_Work.edge
edge_school = handler_School.edge
edge_park = handler_Park.edge


NodeHandler.save_csv('Without_transport' + slash_char + 'friends.csv',  edge_friends)
NodeHandler.save_csv('Without_transport' + slash_char + 'shop.csv', edge_supermarket)
NodeHandler.save_csv('Without_transport' + slash_char + 'home.csv', edge_home)
NodeHandler.save_csv('Without_transport' + slash_char + 'work.csv', edge_work)
NodeHandler.save_csv('Without_transport' + slash_char + 'school.csv', edge_school)
NodeHandler.save_csv('Without_transport' + slash_char + 'park.csv', edge_park)
