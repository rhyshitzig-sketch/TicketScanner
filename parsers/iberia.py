import re
from datetime import date as _date

# Per-page: each boarding card page is one ticket for one passenger.

SIGNALS = [r'\bIB\d{3,5}\b', r'iberia', r'CÓDIGO DE RESERVA']

_MONTHS_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
}

_CONF_LABEL = re.compile(r'RESERVATION CODE', re.IGNORECASE)
_CONF_VALUE = re.compile(r'\b([A-Z]{6})\b')           # Iberia codes are 6 uppercase letters, no digits
_NAME       = re.compile(r'\b([A-Z][A-Z\-]+)/([A-Z]+)\b')
_FROM_LABEL = re.compile(r'DE\s*/\s*FROM', re.IGNORECASE)
_TO_LABEL   = re.compile(r'\bA\s*/\s*TO\b', re.IGNORECASE)
_DATE_TIME  = re.compile(r'(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+(\d{2}:\d{2})', re.IGNORECASE)
_IATA       = re.compile(r'\(([A-Z]{3})\)')
_FLIGHT_NUM = re.compile(r'\b([A-Z]{2}\d{3,5})\b')


def detect(text):
    return 'IBERIA' in text.upper() and 'Tarjeta de embarque' in text


def _after(text, label_re, chars=80):
    m = label_re.search(text)
    return text[m.end():m.end() + chars] if m else ''


def _fmt_datetime(match):
    day   = match[0].zfill(2)
    month = _MONTHS_ES.get(match[1].lower(), '00')
    year  = str(_date.today().year)
    return f'{day}/{month}/{year}', match[2]


def parse(text):
    # Confirmation: first 6-uppercase-letter token after "RESERVATION CODE"
    confirmation = ''
    conf_win = _after(text, _CONF_LABEL, 30)
    ref = _CONF_VALUE.search(conf_win)
    if ref:
        confirmation = ref.group(1)

    # Name: LASTNAME/INITIAL
    name_m = _NAME.search(text)
    last_name  = name_m.group(1) if name_m else ''
    first_name = name_m.group(2) if name_m else ''

    # Origin IATA (first parenthesised code after DE/FROM)
    origin = ''
    from_win = _after(text, _FROM_LABEL, 80)
    iata_m = _IATA.search(from_win)
    if iata_m:
        origin = iata_m.group(1)

    # Destination IATA
    dest = ''
    to_win = _after(text, _TO_LABEL, 80)
    iata_m = _IATA.search(to_win)
    if iata_m:
        dest = iata_m.group(1)

    # Dates/times: find all "DD mon HH:MM" in page order.
    # Avoids the two-column interleaving problem (SALIDA | LLEGADA labels
    # may appear on the same line, pushing the date outside a small window).
    date_times = _DATE_TIME.findall(text)
    date_dep = time_dep = date_arr = time_arr = ''
    if date_times:
        date_dep, time_dep = _fmt_datetime(date_times[0])
    if len(date_times) >= 2:
        date_arr, time_arr = _fmt_datetime(date_times[1])

    # Flight number: first XX####  token in the whole page (BN.035 has a dot so won't match)
    flight_num = ''
    fn = _FLIGHT_NUM.search(text)
    if fn:
        flight_num = fn.group(1)

    return {
        'airline':        'Iberia',
        'last_name':      last_name,
        'first_name':     first_name,
        'flight_number':  flight_num,
        'confirmation':   confirmation,
        'ticket_number':  '',
        'origin':         origin,
        'destination':    dest,
        'route':          f'{origin} - {dest}' if origin else '',
        'date_departure': date_dep,
        'date_arrival':   date_arr,
        'time_departure': time_dep,
        'time_arrival':   time_arr,
    }
