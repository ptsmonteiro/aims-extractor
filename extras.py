from datetime import datetime
import json
import requests
import re

airports_icao = None
airports_iata = {}

sun_api_cache = {}

def load_airport_db():
    global airports_icao
    global airports_iata

    fp = open('airports.json')
    airports_icao = json.load(fp)

    # Create IATA based hash
    for icao in airports_icao:
        airport = airports_icao[icao]
        if not airport['iata']: continue
        airports_iata[airport['iata']] = airport

def get_icao_from_iata(iata):
    global airports_iata
    if len(airports_iata) < 1: load_airport_db()
    return airports_iata[iata]['icao']

def get_night_times(icao, date):
    global sun_api_cache

    print ("Getting twilight times for %s on %s" % (icao, date))
    global airports_icao

    airport = airports_icao[icao]

    # All times are UTC
    url = "https://api.sunrise-sunset.org/json?lat=%s&lng=%s&date=%s" % (
        airport['lat'], airport['lon'], date)

    # Request with cache
    if url in sun_api_cache:
        data = sun_api_cache[url]
    else:
        response = requests.get(url)
        data = response.json()['results']
        sun_api_cache[url] = data

    times = {
        'begin': datetime.strptime(date + ' ' + data['civil_twilight_end'], '%Y-%m-%d %I:%M:%S %p'),
        'end': datetime.strptime(date + ' ' + data['civil_twilight_begin'], '%Y-%m-%d %I:%M:%S %p')
    }

    #print(times)
    #exit()
    return times

def enhance_flight(flight):
    # Normalize date
    flight['Date'] = datetime.strptime(flight['Date'], '%d/%m/%y').date().isoformat()

    # Simulator?
    if len(flight['SimType']) > 0:
        return flight

    # PIC name
    if len(flight['PicName']) > 0:
        flight['PicName'] = flight['PicName'].title()

    # Some proper datetimes
    dep_datetime = datetime.strptime(flight['Date'] + ' ' + flight['DepTime'],
        '%Y-%m-%d %H:%M')
    arr_datetime = datetime.strptime(flight['Date'] + ' ' + flight['ArrTime'],
        '%Y-%m-%d %H:%M')

    # Get ICAO from CSV IATA
    flight['dep_icao'] = get_icao_from_iata(flight['DepPlace'])
    flight['arr_icao'] = get_icao_from_iata(flight['ArrPlace'])

    # Night time, takeoffs and landings
    print("Getting night info")
    ntd = get_night_times(flight['dep_icao'], flight['Date'])
    if dep_datetime > ntd['begin'] or dep_datetime < ntd['end']:
        flight['TKoffsNight'] = 1
    else:
        flight['TKoffsDay'] = 1

    nta = get_night_times(flight['arr_icao'], flight['Date'])
    if arr_datetime > nta['begin'] or arr_datetime < nta['end']:
        flight['LandsNight'] = 1
    else:
        flight['LandsDay'] = 1

    if (flight['LandsNight'] == 1):
        night_begin = night_time_intersect(ntd['begin'], nta['begin'], dep_datetime, arr_datetime)
        night_end = night_time_intersect(ntd['end'], nta['end'], dep_datetime, arr_datetime)

        print("Departure %s" % dep_datetime)
        print("Arrival %s" % arr_datetime)

        print("Departure night begins %s" % ntd['begin'])
        print("Departure night ends %s" % ntd['end'])

        print("In flight night begins %s" % night_begin)
        print("In flight night ends %s" % night_end)

        print("Arrival night begins %s" % nta['begin'])
        print("Arrival night ends %s" % nta['end'])

        night_flight_begin = None
        night_flight_end = None
        if flight['TKoffsNight'] == 1:
            night_flight_begin = dep_datetime
        if flight['LandsNight'] == 1:
            night_flight_end = arr_datetime

        if not night_flight_begin and night_begin > dep_datetime and night_begin < arr_datetime:
            night_flight_begin = night_begin
        if not night_flight_end and night_end > dep_datetime and night_end < arr_datetime:
            night_flight_end = night_end

        if (night_flight_begin and night_flight_end):
            night_flight_time = night_flight_end - night_flight_begin
        else:
            night_flight_time = None

        print("Night flight from %s to %s (%s)" % (
            night_flight_begin, night_flight_end, night_flight_time))
        print("Total flight time %s" % (arr_datetime - dep_datetime))

        #print(str(night_flight_time))
        night_time_str = re.match('^(\d+:\d+):\d+', str(night_flight_time)).group(1)
        flight['NightTime'] =  night_time_str

    else:
        flight['NightTime'] = ''
    
    return flight

def night_time_intersect(night_time_dep, night_time_arr, dep_time, arr_time):
    # intersection between the flight time line and the night time line (0 < t < 1)
    p = (dep_time - night_time_dep) / (
        night_time_arr - night_time_dep + (dep_time - arr_time))

    # returns the actual time of intersection
    return dep_time + p * (arr_time - dep_time)

def enhance_flights(flights):
    enhanced_flights = []
    for flight in flights:
        enhanced_flights.append(enhance_flight(flight))
    return enhanced_flights
