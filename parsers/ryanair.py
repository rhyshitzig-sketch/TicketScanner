import re

DOCUMENT_LEVEL = True

SIGNALS = [
    r'myRyanair',
    r'\bRYANAIR\b',
]

_CONFIRMATION = re.compile(r'N[uú]mero de reserva', re.IGNORECASE)
_BOOKING_REF  = re.compile(r'\b([A-Z][A-Z0-9]{4,7})\b')
_DATE         = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
_DEP_TIME     = re.compile(r'Hora de salida\s*[-–]\s*(\d{2}:\d{2})', re.IGNORECASE)
_ARR_TIME     = re.compile(r'Hora de llegada\s*[-–]\s*(\d{2}:\d{2})', re.IGNORECASE)
_IATA_PAIR    = re.compile(r'\(([A-Z]{3})\)\s*[-–]\s*\(([A-Z]{3})\)')
_FLIGHT_NUM   = re.compile(r'\b(FR\d{3,5})\b')
_TITLE        = re.compile(
    r'^(Sr\.?|Srta\.?|D\.?|Da\.?|Mr\.?|Mrs\.?|Ms\.?|Don|Doña)\s+(.+)$',
    re.IGNORECASE,
)
_VUELO_IDA    = re.compile(r'Vuelo de ida[:\s]+(FR\d+)', re.IGNORECASE)
_VUELO_VUELTA = re.compile(r'Vuelo de vuelta[:\s]*(FR\d+)', re.IGNORECASE)


def detect(text):
    return 'RYANAIR' in text.upper() or 'myRyanair' in text


def parse(text):
    confirmation = _parse_confirmation(text)
    flights      = _parse_flights(text)
    passengers   = _parse_passengers(text)

    results = []
    for pax in passengers:
        for fn in pax['flights']:
            if fn not in flights:
                continue
            fd = flights[fn]
            results.append({
                'airline':        'Ryanair',
                'last_name':      pax['last_name'],
                'first_name':     pax['first_name'],
                'flight_number':  fn,
                'confirmation':   confirmation,
                'ticket_number':  '',
                'origin':         fd['origin'],
                'destination':    fd['destination'],
                'route':          fd['route'],
                'date_departure': fd['date'],
                'date_arrival':   fd['date'],
                'time_departure': fd['dep_time'],
                'time_arrival':   fd['arr_time'],
            })

    return results


def _parse_confirmation(text):
    m = _CONFIRMATION.search(text)
    if not m:
        return ''
    # Search the next 60 chars for an all-uppercase alphanumeric booking ref.
    # No IGNORECASE so mixed-case words like "Lisboa" are skipped automatically.
    ref = _BOOKING_REF.search(text[m.end():m.end() + 60])
    return ref.group(1) if ref else ''


def _parse_flights(text):
    """Extract all flights from the flight info section (before passengers).
    Works regardless of whether pdfplumber interleaves the two-column layout
    or reads each column sequentially, because each list is collected separately
    and zipped by encounter order."""
    end = text.find('Pasajero')
    section = text[:end] if end != -1 else text

    nums   = list(dict.fromkeys(_FLIGHT_NUM.findall(section)))  # unique, ordered
    dates  = _DATE.findall(section)
    deps   = _DEP_TIME.findall(section)
    arrs   = _ARR_TIME.findall(section)
    iatas  = _IATA_PAIR.findall(section)

    flights = {}
    for i, fn in enumerate(nums):
        orig = iatas[i][0] if i < len(iatas) else ''
        dest = iatas[i][1] if i < len(iatas) else ''
        flights[fn] = {
            'date':        dates[i] if i < len(dates) else '',
            'dep_time':    deps[i]  if i < len(deps)  else '',
            'arr_time':    arrs[i]  if i < len(arrs)  else '',
            'origin':      orig,
            'destination': dest,
            'route':       f'{orig} - {dest}' if orig else '',
        }

    return flights


def _parse_passengers(text):
    start = text.find('Pasajero')
    if start == -1:
        return []

    section    = text[start:]
    passengers = []
    current    = None

    for line in section.split('\n'):
        line = line.strip()
        if not line:
            continue

        m = _TITLE.match(line)
        if m:
            if current:
                passengers.append(current)
            current = {**_split_name(m.group(2).strip()), 'flights': []}
            continue

        if current is None:
            continue

        m = _VUELO_IDA.search(line)
        if m:
            current['flights'].append(m.group(1))
            continue

        m = _VUELO_VUELTA.search(line)
        if m:
            current['flights'].append(m.group(1))

    if current:
        passengers.append(current)

    return passengers


def _split_name(full_name):
    """First word → first_name, remainder → last_name (cells are editable for corrections)."""
    parts = full_name.split()
    if len(parts) == 1:
        return {'first_name': '', 'last_name': parts[0]}
    return {'first_name': parts[0], 'last_name': ' '.join(parts[1:])}
