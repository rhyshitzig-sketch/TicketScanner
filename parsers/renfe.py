import re

# Compiled once
_DATE       = re.compile(r'(\d{2}/\d{2}/\d{4})')
_TIME       = re.compile(r'(\d{2}:\d{2})$')
_TRAIN        = re.compile(r'([A-Z]{1,4})\s+(\d{4,6})UNICA')
_TRAIN_INLINE = re.compile(r'\b(AVE|ALVIA|MD|AVANT|REGIONAL|ALTARIA|EUROMED)\s+(\d{4,6})', re.IGNORECASE)
_TRAIN_NUM    = re.compile(r'^(\d{5})$')
_TRAIN_TYPE   = re.compile(r'^(AVE|ALVIA|MD|AVANT|REGIONAL|ALTARIA|EUROMED)\b', re.IGNORECASE)
_DATE_ONLY  = re.compile(r'^\d{2}/\d{2}/\d{4}$')
_TIME_ONLY  = re.compile(r'^\d{2}:\d{2}$')
_NAME       = re.compile(r'^[A-Z]\.[\w\-]+\.?$')
_BILLETE    = re.compile(r'Billete:\s*(\d+)')


def detect(text):
    text_upper = text.upper()
    # Match Renfe only if it doesn't have Iryo branding
    return 'RENFE' in text_upper and 'IRYO' not in text_upper


def parse(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    data = {
        'airline':        'Renfe',
        'last_name':      '',
        'first_name':     '',
        'flight_number':  '',
        'confirmation':   '',
        'ticket_number':  '',
        'origin':         '',
        'destination':    '',
        'route':          '',
        'date_departure': '',
        'date_arrival':   '',
        'time_departure': '',
        'time_arrival':   '',
    }

    # Pre-pass 1: ticket number — separate loop because pdfplumber may combine
    # "Nº Billete:" onto the same line as Origen/Destino, blocking the elif chain.
    for line in lines:
        m = _BILLETE.search(line)
        if m:
            data['ticket_number'] = m.group(1)
            break

    # Pre-pass 2: train number — two layout styles exist:
    #   Style A (Omio/bundled):  "MD 18903UNICA" on the Coche line
    #   Style B (direct Renfe):  "03662" alone + "AVE ESTANDAR" alone on separate lines
    _collect_train_number(lines, data)

    origen_idx = destino_idx = None
    for i, line in enumerate(lines):

        # "Localizador: BMTKXJ CombinadosRodalies: Z7NXD" — take only first word
        if line.startswith('Localizador:'):
            rest = line.split(':', 1)[1].strip()
            data['confirmation'] = rest.split()[0] if rest else ''
            # Omio bundles: name on next line; direct Renfe PDFs: name on previous line
            if i + 1 < len(lines) and _NAME.match(lines[i + 1]):
                _parse_name(lines[i + 1], data)
            elif i > 0 and _NAME.match(lines[i - 1]):
                _parse_name(lines[i - 1], data)

        # "Origen: GIRONA 21/05/2026 06:34"  (Omio style — all inline)
        # "Origen: GIRONA"                    (direct style — date/time on nearby lines)
        elif line.startswith('Origen:'):
            origen_idx = i
            rest = line.split(':', 1)[1].strip()
            dm = _DATE.search(rest)
            tm = _TIME.search(rest)
            if dm:
                data['origin']         = rest[:dm.start()].strip()
                data['date_departure'] = dm.group(1)
            else:
                data['origin'] = rest
            if tm:
                data['time_departure'] = tm.group(1)

        # "Destino: MADRID P.ATOCHA 21/05/2026 10:37"  (Omio)
        # "Destino: MADRID P.ATOCHA"                    (direct)
        elif line.startswith('Destino:'):
            destino_idx = i
            rest = line.split(':', 1)[1].strip()
            dm = _DATE.search(rest)
            tm = _TIME.search(rest)
            if dm:
                data['destination']  = rest[:dm.start()].strip()
                data['date_arrival'] = dm.group(1)
            else:
                data['destination'] = rest
            if tm:
                data['time_arrival'] = tm.group(1)

    # Fallback for direct-Renfe layout: standalone date/time lines near Origen/Destino.
    # Dates float above Origen; times float below Destino.
    if origen_idx is not None:
        _fill_dates_times(lines, origen_idx, destino_idx, data)

    data['route'] = f"{data['origin']} - {data['destination']}"
    return data


def _collect_train_number(lines, data):
    """Extract train number supporting three layout styles:
    A (Omio):   "MD 18903UNICA" on the Coche line
    B (inline): "AVE 03662 ESTANDAR" on one line (pdfplumber column merge)
    C (split):  "03662" alone + "AVE ESTANDAR" alone on separate lines
    """
    train_num = ''
    train_type = ''
    for line in lines:
        # Style A
        if 'UNICA' in line:
            m = _TRAIN.search(line)
            if m:
                data['flight_number'] = m.group(1) + ' ' + m.group(2)
                return
        # Style B
        m = _TRAIN_INLINE.search(line)
        if m:
            data['flight_number'] = m.group(1).upper() + ' ' + m.group(2)
            return
        # Style C — accumulate type and number from separate lines
        if not train_num and _TRAIN_NUM.match(line):
            train_num = line
        if not train_type:
            m = _TRAIN_TYPE.match(line)
            if m:
                train_type = m.group(1).upper()
        if train_num and train_type:
            data['flight_number'] = train_type + ' ' + train_num
            return


def _fill_dates_times(lines, origen_idx, destino_idx, data):
    """Fallback for direct-Renfe PDFs: dates precede Origen, times follow Destino."""
    if not data['date_departure'] or not data['date_arrival']:
        dates_before = [
            lines[j]
            for j in range(max(0, origen_idx - 6), origen_idx)
            if _DATE_ONLY.match(lines[j])
        ]
        if dates_before and not data['date_departure']:
            data['date_departure'] = dates_before[0]
        if not data['date_arrival']:
            data['date_arrival'] = dates_before[1] if len(dates_before) >= 2 else (dates_before[0] if dates_before else '')

    if not data['time_departure'] or not data['time_arrival']:
        start = (destino_idx + 1) if destino_idx is not None else (origen_idx + 2)
        times_after = [
            lines[j]
            for j in range(start, min(start + 8, len(lines)))
            if _TIME_ONLY.match(lines[j])
        ]
        if times_after and not data['time_departure']:
            data['time_departure'] = times_after[0]
        if not data['time_arrival']:
            data['time_arrival'] = times_after[1] if len(times_after) >= 2 else (times_after[0] if times_after else '')


def _parse_name(raw, data):
    # Format: FIRSTINITIAL.LASTNAME[.] e.g. "M.SANTAMAR." or "R.HITZIG-S."
    dot = raw.find('.')
    if dot != -1:
        data['first_name'] = raw[:dot]
        data['last_name']  = raw[dot + 1:].rstrip('.')
    else:
        data['last_name'] = raw
