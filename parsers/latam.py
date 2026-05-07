import re
import unicodedata
from datetime import date as _date

DOCUMENT_LEVEL = True
SIGNALS = [r'LATAM AIRLINES', r'CODIGO DE RES\.', r'LOCALIZADOR AEROLINEA']

_MONTHS = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
    'ene': '01', 'abr': '04', 'ago': '08', 'dic': '12',
}

_CITY_TO_IATA = {
    'GUARULHOS': 'GRU', 'SAO PAULO': 'GRU',
    'LISBON': 'LIS',    'LISBOA': 'LIS',
    'MADRID': 'MAD',    'BARCELONA': 'BCN',
    'EZEIZA': 'EZE',    'BUENOS AIRES': 'EZE',
    'SANTIAGO': 'SCL',  'LIMA': 'LIM',
    'BOGOTA': 'BOG',    'RIO DE JANEIRO': 'GIG',
    'MIAMI': 'MIA',     'NEW YORK': 'JFK',
}

_BOOKING     = re.compile(r'CODIGO DE RES\.\s*:\s*([A-Z0-9]+)', re.IGNORECASE)
_LOCALIZADOR = re.compile(r'LOCALIZADOR AEROLINEA\s*:\s*(?:[A-Z]{2}/)?([A-Z0-9]+)', re.IGNORECASE)
_NAME        = re.compile(r'^([A-Z][A-Z ]+)/([A-Z]+)\s*$')
_VUELO       = re.compile(r'VUELO\s+(LA\s*\d{3,5})', re.IGNORECASE)
_VUELO_YEAR  = re.compile(r'VUELO\s+LA\s*\d+.+?(\d{4})', re.IGNORECASE)
_SALIDA      = re.compile(
    r'SALIDA\s*:\s*(.+?)\s+(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic'
    r'|jan|apr|aug|dec)\s+(\d{2}:\d{2})', re.IGNORECASE)
_LLEGADA     = re.compile(
    r'LLEGADA\s*:\s*(.+?)\s+(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic'
    r'|jan|apr|aug|dec)\s+(\d{2}:\d{2})', re.IGNORECASE)


def detect(text):
    return 'LATAM' in text.upper() and 'CODIGO DE RES' in text.upper()


def _city_to_iata(city_str):
    m = re.search(r'\(([^)]+)\)', city_str)
    if m:
        name = m.group(1).upper()
        for key, iata in _CITY_TO_IATA.items():
            if key in name:
                return iata
    city = city_str.split(',')[0].strip().upper()
    return _CITY_TO_IATA.get(city, city[:3])


def _fmt_date(day, month_str, year):
    month = _MONTHS.get(month_str.lower(), '00')
    return f'{int(day):02d}/{month}/{year}'


def parse(text):
    text  = unicodedata.normalize('NFC', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Confirmation: prefer airline locator over GDS code
    confirmation = ''
    m = _LOCALIZADOR.search(text)
    if m:
        confirmation = m.group(1)
    else:
        m = _BOOKING.search(text)
        if m:
            confirmation = m.group(1)

    # Name: LASTNAME/FIRSTNAME
    last_name = first_name = ''
    for line in lines:
        m = _NAME.match(line)
        if m:
            last_name  = m.group(1).strip()
            first_name = m.group(2).strip()
            break

    # Year from first VUELO header (both flights share same year)
    year = str(_date.today().year)
    m = _VUELO_YEAR.search(text)
    if m:
        year = m.group(1)

    flights = []
    for i, line in enumerate(lines):
        vm = _VUELO.search(line)
        if not vm:
            continue

        flight_number = vm.group(1).replace(' ', '')
        section = '\n'.join(lines[i:i + 15])

        dep_city = dep_date = dep_time = ''
        arr_city = arr_date = arr_time = ''

        sm = _SALIDA.search(section)
        if sm:
            dep_city = _city_to_iata(sm.group(1))
            dep_date = _fmt_date(sm.group(2), sm.group(3), year)
            dep_time = sm.group(4)

        lm = _LLEGADA.search(section)
        if lm:
            arr_city = _city_to_iata(lm.group(1))
            arr_date = _fmt_date(lm.group(2), lm.group(3), year)
            arr_time = lm.group(4)

        flights.append({
            'airline':        'LATAM',
            'flight_number':  flight_number,
            'last_name':      last_name,
            'first_name':     first_name,
            'confirmation':   confirmation,
            'route':          f'{dep_city}-{arr_city}',
            'date_departure': dep_date,
            'date_arrival':   arr_date,
            'time_departure': dep_time,
            'time_arrival':   arr_time,
        })

    return flights
