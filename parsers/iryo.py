import re

DOCUMENT_LEVEL = False

_STATION_TO_IATA = {
    'VALENCIA': 'VLC', 'MADRID': 'MAD',
    'BARCELONA': 'BCN', 'SEVILLA': 'SVQ',
}

def detect(text):
    text_lower = text.lower()
    return 'iryo' in text_lower and 'renfe' in text_lower

def parse(text):
    lines = text.split('\n')

    # Extract confirmation and ticket number
    conf_m = re.search(r'LOCALIZADOR:\s*([A-Z0-9]+)', text)
    confirmation = conf_m.group(1) if conf_m else ''

    ticket_m = re.search(r'BILLETE:\s*(\d+)', text)
    ticket_number = ticket_m.group(1) if ticket_m else ''

    # Extract passenger name (format: FIRSTNAME MIDDLENAME LASTNAME)
    # pdfplumber sometimes splits first letter: "M ARIA" instead of "MARIA"
    first_name = ''
    last_name = ''
    for line in lines:
        line = line.strip()
        if re.match(r'^[A-Z\s]+$', line) and len(line) > 8 and 'LOCALIZADOR' not in line:
            parts = line.split()
            # Fix split first letter: ['M', 'ARIA', ...] → ['MARIA', ...]
            if parts and len(parts[0]) == 1 and len(parts) > 1:
                parts = [parts[0] + parts[1]] + parts[2:]
            if len(parts) >= 2:
                last_name = parts[-1]
                first_name = ' '.join(parts[:-1])
                break

    train_num = ''

    # Extract dates and times - find the "Salida Tren Llegada" section
    # Format: Salida Tren Llegada
    #         19.05.2026 06083 19.05.2026
    #         08:12 10:08
    salida_idx = -1
    for i, line in enumerate(lines):
        if 'Salida' in line and 'Tren' in line:
            salida_idx = i
            break

    dep_day, dep_month, dep_year = '01', '01', '2026'
    dep_time = '00:00'
    arr_day, arr_month, arr_year = '01', '01', '2026'
    arr_time = '00:00'

    if salida_idx >= 0 and salida_idx + 2 < len(lines):
        # Next line has dates and train number: "19.05.2026 06083 19.05.2026"
        dates_line = lines[salida_idx + 1].strip()
        train_m = re.search(r'\d+\.\d+\.\d+\s+(\d+)\s+\d+\.\d+\.\d+', dates_line)
        if train_m:
            train_num = train_m.group(1)
        dates = re.findall(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', dates_line)
        if len(dates) >= 2:
            dep_day, dep_month, dep_year = dates[0]
            arr_day, arr_month, arr_year = dates[1]

        # Next line has times
        times_line = lines[salida_idx + 2].strip()
        times = re.findall(r'(\d{2}):(\d{2})', times_line)
        if len(times) >= 2:
            dep_time = f'{times[0][0]}:{times[0][1]}'
            arr_time = f'{times[1][0]}:{times[1][1]}'

    # Route line has both cities on the same line e.g. "Valencia-Joaquín Madrid-Chamartín"
    known_cities = list(_STATION_TO_IATA.keys())
    origin = ''
    destination = ''
    for line in lines[:5]:
        line_upper = line.upper()
        hits = sorted([(line_upper.find(c), c) for c in known_cities if c in line_upper])
        if len(hits) >= 2:
            origin = hits[0][1]
            destination = hits[1][1]
            break
        elif len(hits) == 1 and not origin:
            origin = hits[0][1]
        elif len(hits) == 1 and origin:
            destination = hits[0][1]
            break

    origin_iata = _STATION_TO_IATA.get(origin, origin[:3] if origin else '')
    dest_iata = _STATION_TO_IATA.get(destination, destination[:3] if destination else '')

    flights = []
    if origin_iata and dest_iata:
        flights.append({
            'airline': 'Iryo',
            'flight_number': train_num,
            'origin': origin_iata,
            'destination': dest_iata,
            'route': f'{origin_iata} - {dest_iata}',
            'date_departure': f'{dep_day}/{dep_month}/{dep_year}',
            'date_arrival': f'{arr_day}/{arr_month}/{arr_year}',
            'time_departure': dep_time,
            'time_arrival': arr_time,
            'confirmation': confirmation,
            'ticket_number': ticket_number,
            'last_name': last_name,
            'first_name': first_name,
        })

    return flights
