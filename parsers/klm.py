import re
from datetime import date as _date

DOCUMENT_LEVEL = True
SIGNALS = [r'\bKL\s*\d{3,5}\b', r'KLM\s+ROYAL', r'BOOKING\s+REF']

_MONTHS = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}

_CITY_TO_IATA = {
    'CARDIFF': 'CDF', 'AMSTERDAM': 'AMS', 'SCHIPHOL': 'AMS',
    'VALENCIA': 'VLC', 'LONDON': 'LHR', 'PARIS': 'CDG',
}


def detect(text):
    return 'BOOKING REF:' in text and 'KLM' in text.upper()


def parse(text):
    lines = text.split('\n')

    booking_ref = ''
    for line in lines:
        m = re.search(r'BOOKING REF:\s*([A-Z0-9]+)', line)
        if m:
            booking_ref = m.group(1)
            break

    last_name = ''
    first_name = ''
    for line in lines:
        m = re.match(r'^([A-Z\-]+)/([A-Z\s]+)$', line.strip())
        if m:
            last_name = m.group(1)
            first_name = m.group(2).strip()
            break

    flights = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('FLIGHT '):
            flight_m = re.search(r'FLIGHT\s+([A-Z0-9\s]+?)\s*-\s*', line)
            if flight_m:
                flight_num = flight_m.group(1).strip()

                dep_info = None
                arr_info = None
                for j in range(i + 1, min(i + 10, len(lines))):
                    if not dep_info and lines[j].strip().startswith('DEPARTURE:'):
                        dep_m = re.search(
                            r'DEPARTURE:\s*([A-Z ,()]+?)\s+(\d{1,2})\s+([A-Z]{3})\s+(\d{2}):(\d{2})',
                            lines[j]
                        )
                        if dep_m:
                            dep_info = dep_m
                    elif not arr_info and lines[j].strip().startswith('ARRIVAL:'):
                        arr_m = re.search(
                            r'ARRIVAL:\s*([A-Z ,()]+?)\s+(\d{1,2})\s+([A-Z]{3})\s+(\d{2}):(\d{2})',
                            lines[j]
                        )
                        if arr_m:
                            arr_info = arr_m
                    if dep_info and arr_info:
                        break

                if dep_info and arr_info:
                    dep_city = dep_info.group(1).strip()
                    dep_day = dep_info.group(2).zfill(2)
                    dep_mon = _MONTHS.get(dep_info.group(3).lower(), '00')
                    dep_year = str(_date.today().year)
                    dep_time = f'{dep_info.group(4)}:{dep_info.group(5)}'

                    arr_city = arr_info.group(1).strip()
                    arr_day = arr_info.group(2).zfill(2)
                    arr_mon = _MONTHS.get(arr_info.group(3).lower(), '00')
                    arr_year = str(_date.today().year)
                    arr_time = f'{arr_info.group(4)}:{arr_info.group(5)}'

                    dep_iata = _extract_iata(dep_city)
                    arr_iata = _extract_iata(arr_city)

                    flights.append({
                        'airline': 'KLM',
                        'flight_number': flight_num,
                        'origin': dep_iata,
                        'destination': arr_iata,
                        'route': f'{dep_iata} - {arr_iata}',
                        'date_departure': f'{dep_day}/{dep_mon}/{dep_year}',
                        'date_arrival': f'{arr_day}/{arr_mon}/{arr_year}',
                        'time_departure': dep_time,
                        'time_arrival': arr_time,
                        'confirmation': booking_ref,
                        'ticket_number': '',
                        'last_name': last_name,
                        'first_name': first_name,
                    })

        i += 1

    return flights


def _extract_iata(city_str):
    m = re.search(r'\(([A-Z]{3})\)', city_str)
    if m:
        return m.group(1)
    # Extract city name and look it up
    parts = city_str.split(',')
    city = parts[0].strip().upper() if parts else ''
    return _CITY_TO_IATA.get(city, city[:3] if city else '')
