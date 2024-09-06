The Python script main.py includes a function to parse command-line arguments using the argparse module. This allows you to customize the number of trips and persons in the simulation by passing arguments when you run the script.
If you need to change map, public transport, etc. Please read Sumo_config.md 
Available Arguments:
-t: Defines the number of trips each person will take in the simulation.
Default value: 10
-p: Defines the number of persons to simulate.
Default value: 1

To run the simulation with default values:
python main.py

To customize the number of trips and persons, use the following format, but without []:
python main.py -t [number_of_trips] -p [number_of_persons]