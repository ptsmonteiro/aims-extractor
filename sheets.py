#from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
from datetime import date, datetime
import re
import time

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
    return last['activity']['datetime'] if last['activity'] else None

def get_last_entry_and_subtotals():
    print("Getting last entry from Google Sheet Logbook")

    all_flight_dates = sheet.col_values(1)
    all_sim_dates = sheet.col_values(23)

    # last activity and last page subtotals
    activity_entry = None
    subtotals_entry = None

    i = len(all_flight_dates) - 1
    while ((not activity_entry or not subtotals_entry) and i > 0):

        # 'TOTAL ACC' entry
        if (all_flight_dates[i] == 'TOTAL ACC'):
            match = re.search(r'(\d+)$', all_flight_dates[i-1])
            if not match:
                raise RuntimeError('Page number expected at %s', i-1) 
            last_page = int(match.group(1))
            if (not subtotals_entry):
                subtotals_entry = {'row': i, 'page': last_page}
        # Date
        elif re.search(r'\d+\-\d+\-\d+$', all_flight_dates[i]):
            flight_date = datetime.strptime(all_flight_dates[i], '%d-%m-%Y').date()
            activity_entry = {'row': i + 1, 'date': flight_date}

        i = i - 1

    # last simulator
    i = len(all_sim_dates) - 1
    while (activity_entry and (i > activity_entry['row'] - 1)):
        if len(all_sim_dates[i]) > 0:
            sim_date = datetime.strptime(all_sim_dates[i], '%d-%m-%Y').date()
            activity_entry = {'row': i + 1, 'date': sim_date}
        i = i - 1

    last = {'activity': activity_entry, 'subtotals': subtotals_entry}
    print(last)
    return last

def insert_flight(flight, last):
    print("Insert flight:")
    print(flight)

    # Stop at future activities
    if date.fromisoformat(flight['Date']) > date.today():
        raise RuntimeError("Trying to import future flights (not yet taken place).")

    # Skip older activities
    flight_datetime = datetime.fromisoformat(flight['Date'] + 'T' + flight['DepTime'])
    if last['activity'] and flight_datetime <= last['activity']['datetime']:
        raise RuntimeError("Trying to import an older activity (maybe already inserted).")

    if last['activity']:
        row = last['activity']['row'] + 1
    else:
        row = last['subtotals']['row'] - FLIGHTS_PER_PAGE

    if (row == last['subtotals']['row']):
        row = last['subtotals']['row'] + 2
        last = create_new_subtotals(last)

    date_range = ""
    row_range = ""

    # Simulator
    if len(flight['SimType']) > 0:
        rowdata = [
            flight['Date'],
            'A' + flight['ACType'],
            flight['SimTime'],
            flight['SimType']
        ]
        date_range = "W%s" % (row)
        row_range = "W%s:Z%s" % (row,row)
    # Flight
    else:
        rowdata = [
            flight['Date'],
            flight['dep_icao'],
            flight['DepTime'],
            flight['arr_icao'],
            flight['ArrTime'],
            'A' + flight['ACType'],
            flight['Reg'],
            '',
            '',
            flight['FltTime'], # multi pilot
            flight['FltTime'], # total time
            flight['PicName'],
            flight['TKoffsDay'],
            flight['TKoffsNight'],
            flight['LandsDay'],
            flight['LandsNight'],
            flight['NightTime'],
            flight['FltTime'], # IFR
            flight['PIC'],
            flight['CoPlt'],
            '', # Dual
            '', # Instructor
        ]
        date_range = "A%s" % (row)
        row_range = "A%s:V%s" % (row,row)

    print(rowdata)

    time.sleep(2)
    sheet.format(date_range, {
        'numberFormat': {
            'type': 'DATE', 'pattern': 'dd-mm-yyyy'
        }
    })
    sheet.update(row_range, [rowdata], 
        value_input_option = gspread.worksheet.ValueInputOption.user_entered)

    if not last['activity']: last['activity'] = {} 

    last['activity']['row'] = row
    last['activity']['datetime'] = datetime.fromisoformat(flight['Date'] + ' ' + flight['DepTime'])

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
