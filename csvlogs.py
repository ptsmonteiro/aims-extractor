import csv
import glob

def get_incoming_flights():
    flights = []

    path = 'incoming/*.csv'
    csv_files = glob.glob(path)

    for f in csv_files:
        print("Processing %s" % f)
        with open(f, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                flights.append(row)

    # TODO move processed flight csv files

    return flights