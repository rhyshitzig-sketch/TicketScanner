import re
from datetime import date as _date, timedelta

DOCUMENT_LEVEL = True

SIGNALS = [r'\bV7\s+\d{3,4}\b']

_MONTHS_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
}

_CONFIRMATION  = re.compile(r'de\s+reserva\s+([A-Z0-9]{5,8})', re.IGNORECASE)
_DATE_HEADER   = re.compile(r'^(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[^:]*:$', re.IGNORECASE)
# pdfplumber outputs both times on one line and both cities on the next:
#   "07.30h 08.55h"
#   "Asturias Valencia"
#   "V7 3582"
_TIMES_PAIR    = re.compile(r'^(\d{2})[.:](\d{2})h?\s+(\d{2})[.:](\d{2})h?$', re.IGNORECASE)
_CITIES_PAIR   = re.compile(r'^(\S+)\s+(\S+)$')
_FLIGHT_LINE   = re.compile(r'^(V7\s*\d+)$', re.IGNORECASE)
_TITLE_PREFIX  = re.compile(r'^(?:MR|MRS?|MS|SR|SRA|SRTA)\.?\s+', re.IGNORECASE)


def detect(text):
    return bool(re.search(r'\bV7\s+\d{3,4}\b', text))


def parse(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    confirmation = ''
    m = _CONFIRMATION.search(text)
    if m:
        confirmation = m.group(1)

    flights    = _parse_flights(lines)
    passengers = _parse_passengers(lines)

    rows = []
    for flight in flights:
        for pax in passengers:
            rows.append({
                'airline':        'Volotea',
                'last_name':      pax['last_name'],
                'first_name':     pax['first_name'],
                'confirmation':   confirmation,
                'ticket_number':  '',
                **flight,
            })
    return rows


def _parse_flights(lines):
    flights = []
    i = 0
    while i < len(lines):
        dh = _DATE_HEADER.match(lines[i])
        if dh and i + 3 < len(lines):
            dep_day   = dh.group(1).zfill(2)
            dep_mon   = _MONTHS_ES.get(dh.group(2).lower(), '00')
            year      = str(_date.today().year)
            dep_date  = f'{dep_day}/{dep_mon}/{year}'

            times_m  = _TIMES_PAIR.match(lines[i + 1])
            cities_m = _CITIES_PAIR.match(lines[i + 2])
            flight_m = _FLIGHT_LINE.match(lines[i + 3])

            if times_m and cities_m and flight_m:
                dep_time   = f'{times_m.group(1)}:{times_m.group(2)}'
                arr_time   = f'{times_m.group(3)}:{times_m.group(4)}'
                origin     = cities_m.group(1)
                dest       = cities_m.group(2)
                flight_num = flight_m.group(1).strip()

                dep_mins = int(times_m.group(1)) * 60 + int(times_m.group(2))
                arr_mins = int(times_m.group(3)) * 60 + int(times_m.group(4))
                if arr_mins < dep_mins:
                    d = _date(int(year), int(dep_mon), int(dep_day))
                    arr_date = (d + timedelta(days=1)).strftime('%d/%m/%Y')
                else:
                    arr_date = dep_date

                flights.append({
                    'flight_number':  flight_num,
                    'origin':         origin,
                    'destination':    dest,
                    'route':          f'{origin} - {dest}',
                    'date_departure': dep_date,
                    'date_arrival':   arr_date,
                    'time_departure': dep_time,
                    'time_arrival':   arr_time,
                })
                i += 4
                continue
        i += 1
    return flights


def _parse_passengers(lines):
    seen = set()
    passengers = []
    for line in lines:
        if not _TITLE_PREFIX.match(line):
            continue
        name = _TITLE_PREFIX.sub('', line).strip()
        # Strip trailing baggage info "1 x 20 Kg" or similar
        name = re.sub(r'\s+\d+\s*[xX]\s*\d+.*$', '', name).strip()
        # Strip trailing "(Adulto)" or similar parenthetical
        name = re.sub(r'\s+\([^)]+\)\s*$', '', name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        parts = name.split()
        passengers.append({
            'first_name': parts[0],
            'last_name':  ' '.join(parts[1:]) if len(parts) > 1 else '',
        })
    return passengers
