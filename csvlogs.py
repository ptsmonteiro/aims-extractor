import csv

def get_incoming_flights(file_path):
    flights = []

    print(f"Reading flights from {file_path}")
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            flights.append(row)

    return flights
