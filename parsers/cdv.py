import re

_MONTHS = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
}
_DATE_ES      = re.compile(r'(\d{1,2}) de (\w+) de (\d{4})', re.IGNORECASE)
_IATA_TIME    = re.compile(r'\b([A-Z]{3})\s+(\d{2}:\d{2})')
_VUELO        = re.compile(r'Vuelo\s+(\S+)')
_PASS         = re.compile(r'^([A-Z][A-Z\s\-]+),\s+([A-Z][A-Z\s]+)$')
_TICKET_NUM   = re.compile(r'\b(\d{3}\s\d{10})\b')
_LOC_AERO     = re.compile(r'Loc\.\s*Aerol[ií]nea:\s*(\S+)', re.IGNORECASE)
_AIRLINE_STOP = re.compile(r'\b(Salida|Llegada|Duraci[oó]n|Operado|Vuelo)\b', re.IGNORECASE)


def detect(text):
    return 'TRAYECTO 1:' in text


def _es_date(line):
    m = _DATE_ES.search(line)
    if not m:
        return ''
    month = _MONTHS.get(m.group(2).lower(), '00')
    return f'{int(m.group(1)):02d}/{month}/{m.group(3)}'


def parse(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    confirmation  = ''
    ticket_number = ''
    last_name     = ''
    first_name    = ''

    for i, line in enumerate(lines):
        m = _LOC_AERO.search(line)
        if m:
            confirmation = m.group(1)
        m = _TICKET_NUM.search(line)
        if m:
            ticket_number = m.group(1)
        m = _PASS.match(line)
        if m and 'AEROPUERTO' not in line and 'TRAYECTO' not in line:
            last_name  = m.group(1).strip()
            first_name = m.group(2).strip()

    trayecto_starts = [i for i, l in enumerate(lines) if re.match(r'TRAYECTO \d+:', l)]

    tickets = []
    for t, start in enumerate(trayecto_starts):
        end     = trayecto_starts[t + 1] if t + 1 < len(trayecto_starts) else len(lines)
        section = lines[start:end]

        airline       = ''
        flight_number = ''
        iata_times    = []
        dates         = []

        for i, line in enumerate(section):
            if re.match(r'Aerol[ií]nea', line, re.IGNORECASE):
                candidate = line.split(None, 1)[1] if re.match(r'Aerol[ií]nea\s+\S', line, re.IGNORECASE) else (section[i + 1] if i + 1 < len(section) else '')
                stop = _AIRLINE_STOP.search(candidate)
                airline = candidate[:stop.start()].strip() if stop else candidate.strip()

            m = _VUELO.search(line)
            if m:
                flight_number = m.group(1)

            for iata, time in _IATA_TIME.findall(line):
                iata_times.append((iata, time))

            d = _es_date(line)
            if d and d not in dates:
                dates.append(d)

        dep_iata = iata_times[0][0] if len(iata_times) > 0 else ''
        dep_time = iata_times[0][1] if len(iata_times) > 0 else ''
        arr_iata = iata_times[1][0] if len(iata_times) > 1 else ''
        arr_time = iata_times[1][1] if len(iata_times) > 1 else ''
        dep_date = dates[0] if dates else ''
        arr_date = dates[-1] if dates else ''

        tickets.append({
            'last_name':      last_name,
            'first_name':     first_name,
            'airline':        airline,
            'flight_number':  flight_number,
            'confirmation':   confirmation,
            'ticket_number':  ticket_number,
            'route':          f'{dep_iata}-{arr_iata}',
            'date_departure': dep_date,
            'date_arrival':   arr_date,
            'time_departure': dep_time,
            'time_arrival':   arr_time,
        })

    return tickets
