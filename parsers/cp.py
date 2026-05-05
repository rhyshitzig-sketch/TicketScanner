import re

# Per-page: each page is one ticket for one passenger.
# T&C pages also contain "Comboios de Portugal" but never have "Nome:", so
# the detect() function uses both checks to avoid false matches.

_HEADER  = re.compile(
    r'Ida:\s*(\d{2}:\d{2})\s+(.+?)\s*>>\s*(\d{2}:\d{2})\s+(.+?)\s+Data:\s*(\d{4}-\d{2}-\d{2})',
    re.IGNORECASE,
)
_TRAIN   = re.compile(r'(Intercidades|Alfa Pendular|Alfa|Regional|R[áa]pido)\s+n\S*\s*(\d+)', re.IGNORECASE)
_NAME    = re.compile(r'Nome:\s*(.+?)(?=\s+Passaporte:|\s*\n)', re.IGNORECASE)
_TICKET  = re.compile(r'Bilhete\s+n\S*\s*(\d+[-/]\d+)', re.IGNORECASE)


def detect(text):
    return 'Comboios de Portugal' in text and bool(_NAME.search(text))


def parse(text):
    header_m = _HEADER.search(text)
    train_m  = _TRAIN.search(text)
    name_m   = _NAME.search(text)
    ticket_m = _TICKET.search(text)

    dep_time = header_m.group(1) if header_m else ''
    origin   = header_m.group(2).strip() if header_m else ''
    arr_time = header_m.group(3) if header_m else ''
    dest     = header_m.group(4).strip() if header_m else ''

    date_str = ''
    if header_m:
        y, m, d = header_m.group(5).split('-')
        date_str = f'{d}/{m}/{y}'

    train_num = ''
    if train_m:
        train_num = train_m.group(1).title() + ' ' + train_m.group(2)

    full_name = name_m.group(1).strip() if name_m else ''
    parts = full_name.split()
    first_name = ' '.join(parts[:-1]) if len(parts) > 1 else ''
    last_name  = parts[-1] if parts else ''

    return {
        'airline':        'CP',
        'last_name':      last_name,
        'first_name':     first_name,
        'flight_number':  train_num,
        'confirmation':   '',
        'ticket_number':  ticket_m.group(1) if ticket_m else '',
        'origin':         origin,
        'destination':    dest,
        'route':          f'{origin} - {dest}' if origin else '',
        'date_departure': date_str,
        'date_arrival':   date_str,
        'time_departure': dep_time,
        'time_arrival':   arr_time,
    }
