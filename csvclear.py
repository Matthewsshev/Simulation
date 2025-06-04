import pandas as pd
from analyse import get_journeys, get_duration, save_journeys
from datetime import datetime, timedelta

def main():
    data = pd.read_csv('sql2csvlarge.csv')
    journeys = get_journeys(data)
    bad_journeys = []
    for journey in journeys:
        for trip in journey:
            type = data['type'][trip]
            if type == 'T':
                duration = get_duration(data, trip)
                if duration >= timedelta(hours=3):
                    print(f' Duration {duration} data {type}')
                    bad_journeys.append(trip)

    print(f'Check bad journeys: Len {len(bad_journeys)} % {len(journeys)}')
    journeys.remove(bad_journeys)
    print(f'Check len {len(journeys)}')

if __name__ == '__main__':
    main()