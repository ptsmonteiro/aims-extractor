import aims
import extras
import sheets
import csvlogs

sheets.init()
#from_date = sheets.get_last_entry_date()

#aims.init()
#flights = aims.get_flights(from_date)
#aims.quit()

flights = csvlogs.get_incoming_flights()
last = sheets.get_last_entry_and_subtotals()
for f in flights:
    sheets.insert_flight(extras.enhance_flight(f), last)
