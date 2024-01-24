import csv
import glob
import shutil

def get_incoming_flights():
    flights = []

    path = 'incoming/*.csv'
    csv_files = glob.glob(path)

    for f in csv_files:
        print(f"Reading flights from {f}")
        with open(f, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                flights.append(row)

        print(f"Moving {f} to processed folder...")
        shutil.move(f, 'processed/')

    return flights