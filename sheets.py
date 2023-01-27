#from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
from datetime import date, time, datetime
import re

FLIGHTS_PER_PAGE = 20

SCOPES = ["https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
    'https://www.googleapis.com/auth/spreadsheets.editor']

config = None
sheet = None

def init():
    global sheet

    global config
    with open('config.json') as json_file:
        data = json.load(json_file)
        config = data['sheets']

    client = gspread.service_account(filename="keys/aims-extractor.json")
    sheet = client.open_by_key(config['spreadsheet_id']).sheet1

def get_last_entry_date():
    last = get_last_entry_and_subtotals()
    return last['activity']['date']

def get_last_entry_and_subtotals():
    print("Getting last entry from Google Sheet Logbook")

    all_flight_dates = sheet.col_values(1)
    all_sim_dates = sheet.col_values(23)

    # last activity and last page subtotals
    activity_entry = None
    subtotals_entry = None

    i = len(all_flight_dates) - 1
    while (not activity_entry or not subtotals_entry and i > 0):

        # 'TOTAL ACC' entry
        if (all_flight_dates[i] == 'TOTAL ACC'):
            match = re.search(r'(\d+)$', all_flight_dates[i-1])
            if not match:
                raise RuntimeError('Page number expected at %s', i-1) 
            last_page = int(match.group(1))
            if (not subtotals_entry):
                subtotals_entry = {'row': i, 'page': last_page}
        # Date
        elif (not re.search(r'PAGINA (\d+)$', all_flight_dates[i]) and len(all_flight_dates[i]) > 0):
            flight_date = datetime.strptime(all_flight_dates[i], '%d-%m-%Y').date()
            activity_entry = {'row': i + 1, 'date': flight_date}

        i = i - 1

    # last simulator
    i = len(all_sim_dates) - 1
    while (i > activity_entry['row']):
        if len(all_sim_dates[i]) > 0:
            sim_date = datetime.strptime(all_sim_dates[i], '%d-%m-%Y').date()
            activity_entry = {'row': i, 'date': sim_date}
        i = i - 1

    last = {'activity': activity_entry, 'subtotals': subtotals_entry}
    print(last)
    return last

def insert_flight(flight, last):
    print("Insert flight:")
    print(flight)

    row = last['activity']['row'] + 1

    if (row == last['subtotals']['row']):
        row = last['subtotals']['row'] + 2
        last = create_new_subtotals(last)

    sheet.update("A%s" % (row), flight['Date'])
    sheet.update("B%s" % (row), flight['dep_icao'])
    sheet.update("D%s" % (row), flight['arr_icao'])

    last['activity']['row'] = row
    last['activity']['Date'] = flight['Date']

    return last

def create_new_subtotals(last):
    global sheet

    print ("Creating new page subtotals")

    page = last['subtotals']['page']

    source_base_row = last['subtotals']['row']
    dest_base_row = source_base_row + FLIGHTS_PER_PAGE + 2

    source_range = "%s:%s" % (source_base_row, source_base_row + 1)
    dest_range = "%s:%s" % (dest_base_row, dest_base_row + 1)

    # Check existing cell contents before overwriting
    if sheet.cell(dest_base_row, 1).value:
        raise RuntimeError("Refusing to overwrite subtotals header")

    sheet.copy_range(source_range, dest_range, paste_type='PASTE_NORMAL', paste_orientation='NORMAL')

    page_cell = "A%s" % (dest_base_row)
    new_page = page + 1
    sheet.update(page_cell, "PAGINA %d" % (new_page))

    last['subtotals']['row'] = dest_base_row
    last['subtotals']['page'] = new_page

    return last
