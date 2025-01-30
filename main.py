import extras
import sheets
import csvlogs
import glob
import shutil

sheets.init()

# List files in incoming folder
path = 'incoming/*.csv'
csv_files = glob.glob(path)

# Process each file in the incoming folder
for file_path in csv_files:

    flights = csvlogs.get_incoming_flights(file_path)
    last = sheets.get_last_entry_and_subtotals()
    for f in flights:
        last = sheets.insert_flight(extras.enhance_flight(f), last)

    print(f"Moving {file_path} to processed folder...")
    shutil.move(file_path, 'processed/')
