import re
import unicodedata
from datetime import date as _date

SIGNALS = [r'\bEJU\d{3,5}\b', r'easyJet']

_MONTHS_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
}

_NAME     = re.compile(r'^([A-ZÁÉÍÓÚÜÑ ]+),\s+([A-ZÁÉÍÓÚÜÑ]+)(?:\s+(?:SRA?|SR|MRS?|MS|MISS)\.?)?\s*$', re.IGNORECASE)
_DATE     = re.compile(r'\b(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b', re.IGNORECASE)
_FLIGHT   = re.compile(r'\b(EJU\d{3,5})\b')
_DEP_TIME = re.compile(r'Salida\s+(\d{2}:\d{2})', re.IGNORECASE)
_ARR_TIME = re.compile(r'Llegada\s+(\d{2}:\d{2})', re.IGNORECASE)
_CONFIRM  = re.compile(r'^([A-Z0-9]{6,8})\s+S\d+\s+S\d+')
_IATA     = re.compile(r'^([A-Z]{3})$')


def detect(text):
    return bool(_FLIGHT.search(text))


def parse(text):
    text  = unicodedata.normalize('NFC', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    last_name = first_name = ''
    flight_number = dep_time = arr_time = dep_date = confirmation = ''
    iata_codes = []

    for line in lines:
        if not last_name:
            m = _NAME.match(line)
            if m:
                last_name  = m.group(1).strip()
                first_name = m.group(2).strip()

        if not flight_number:
            m = _FLIGHT.search(line)
            if m:
                flight_number = m.group(1)

        if not dep_time:
            m = _DEP_TIME.search(line)
            if m:
                dep_time = m.group(1)

        if not arr_time:
            m = _ARR_TIME.search(line)
            if m:
                arr_time = m.group(1)

        if not dep_date:
            m = _DATE.search(line)
            if m:
                day      = m.group(1).zfill(2)
                month    = _MONTHS_ES.get(m.group(2).lower(), '00')
                dep_date = f'{day}/{month}/{_date.today().year}'

        if not confirmation:
            m = _CONFIRM.match(line)
            if m:
                confirmation = m.group(1)

        if _IATA.match(line):
            iata_codes.append(line)

    origin      = iata_codes[0] if len(iata_codes) > 0 else ''
    destination = iata_codes[1] if len(iata_codes) > 1 else ''
    route       = f'{origin}-{destination}' if origin and destination else ''

    return {
        'airline':        'easyJet',
        'flight_number':  flight_number,
        'last_name':      last_name,
        'first_name':     first_name,
        'confirmation':   confirmation,
        'route':          route,
        'date_departure': dep_date,
        'date_arrival':   dep_date,
        'time_departure': dep_time,
        'time_arrival':   arr_time,
    }
