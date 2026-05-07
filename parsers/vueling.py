import re
import unicodedata

DOCUMENT_LEVEL = True

# Any one of these matching is enough to identify a Vueling document.
# Uses multiple signals because logos are images (not text) and encodings vary.
SIGNALS = [
    r'\bVY\d{4}\b',           # Vueling flight numbers (VY8460, etc.)
    r'C[oó]digo de reserva',  # booking ref label
]

_MONTHS = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
}

# Avoid depending on the accented ó — match "reserva:" directly instead
_CONFIRMATION = re.compile(r'\breserva\s*:\s*([A-Z0-9]{4,10})\b', re.IGNORECASE)
# "21 mayo 2026" — Vueling omits "de" between day/month/year
_DATE_VY      = re.compile(
    r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto'
    r'|septiembre|octubre|noviembre|diciembre)\s+(\d{4})', re.IGNORECASE)
_TIME_PAIR    = re.compile(r'(\d{2}:\d{2})h?\s+(\d{2}:\d{2})h?')
_IATA_PAIR    = re.compile(r'\b([A-Z]{3})\b\s+\b([A-Z]{3})\b')
_FLIGHT_NUM   = re.compile(r'\bVY\d+\b')
_PASS_NOISE   = re.compile(
    r'(Asiento|equipaje|compartimento|superior|Ida\b|Vuelta\b|Máx|pieza|Pasajeros)',
    re.IGNORECASE)


def detect(text):
    # "vueling" is a vector logo — not extracted by pdfplumber.
    # "Código de reserva:" is Vueling-specific and always present as text.
    return bool(re.search(r'C[oó]digo de reserva', text, re.IGNORECASE))


def _es_date(text):
    m = _DATE_VY.search(text)
    if not m:
        return ''
    month = _MONTHS.get(m.group(2).lower(), '00')
    return f'{int(m.group(1)):02d}/{month}/{m.group(3)}'


def parse(text):
    text  = unicodedata.normalize('NFC', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    confirmation = ''
    for line in lines:
        m = _CONFIRMATION.search(line)
        if m:
            confirmation = m.group(1)
            break

    flights    = _parse_flights(lines)
    passengers = _parse_passengers(lines)

    rows = []
    for flight in flights:
        for passenger in passengers:
            rows.append({
                **flight,
                **passenger,
                'confirmation':  confirmation,
                'ticket_number': '',
            })
    return rows


def _parse_flights(lines):
    flights = []
    for i, line in enumerate(lines):
        if not re.match(r'^(Ida|Vuelta)\b', line, re.IGNORECASE):
            continue
        section = lines[i:i + 10]

        dep_iata = arr_iata = dep_time = arr_time = flight_number = ''
        date = ''

        for sline in section[:3]:
            date = _es_date(sline)
            if date:
                break

        for sline in section[1:]:
            if not dep_iata:
                m = _IATA_PAIR.search(sline)
                if m:
                    dep_iata, arr_iata = m.group(1), m.group(2)
                    continue
            if not dep_time:
                m = _TIME_PAIR.search(sline)
                if m:
                    dep_time, arr_time = m.group(1), m.group(2)
                    continue
            if not flight_number:
                m = _FLIGHT_NUM.search(sline)
                if m:
                    flight_number = m.group(0)
                    break

        if flight_number:
            flights.append({
                'airline':        'Vueling',
                'flight_number':  flight_number,
                'route':          f'{dep_iata}-{arr_iata}',
                'date_departure': date,
                'date_arrival':   date,
                'time_departure': dep_time,
                'time_arrival':   arr_time,
            })
    return flights


def _parse_passengers(lines):
    # Find the passenger section: starts at first "Pasajeros" line
    start = None
    end   = len(lines)
    for i, line in enumerate(lines):
        if start is None and re.search(r'Pasajeros', line, re.IGNORECASE):
            start = i + 1
        elif start is not None and re.search(r'IMPORTANTE', line, re.IGNORECASE):
            end = i
            break

    if start is None:
        return []

    passengers = []
    for line in lines[start:end]:
        if line.startswith('•'):
            continue
        if re.search(r'\d', line):
            continue
        if _PASS_NOISE.search(line):
            continue
        words = line.split()
        if len(words) < 2:
            continue
        if not all(w[0].isupper() for w in words if w):
            continue
        # Last word = last name, everything before = first name
        passengers.append({
            'last_name':  words[-1],
            'first_name': ' '.join(words[:-1]),
        })

    return passengers
