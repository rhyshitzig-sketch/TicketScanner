import io
import copy
import re
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

COLUMNS = [
    ('last_name',       'Last Name'),
    ('first_name',      'First Name'),
    ('airline',         'Airline'),
    ('flight_number',   'Flight Number'),
    ('confirmation',    'Confirmation Number'),
    ('ticket_number',   'Ticket Number'),
    ('route',           'Flight Route'),
    ('date_departure',  'Date of Departure'),
    ('date_arrival',    'Date of Arrival'),
    ('time_departure',  'Time of Departure'),
    ('time_arrival',    'Time of Arrival'),
]

HEADER_FONT  = Font(bold=True, color='FFFFFF')
HEADER_FILL  = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
HEADER_ALIGN = Alignment(horizontal='center', vertical='center')


MONTHS_ES = {
    '01': 'ENERO',
    '02': 'FEBRERO',
    '03': 'MARZO',
    '04': 'ABRIL',
    '05': 'MAYO',
    '06': 'JUNIO',
    '07': 'JULIO',
    '08': 'AGOSTO',
    '09': 'SEPTIEMBRE',
    '10': 'OCTUBRE',
    '11': 'NOVIEMBRE',
    '12': 'DICIEMBRE',
}

TEMPLATE_COLUMNS = {
    'first_name': 'D',
    'last_name': 'E',
    'passport': 'F',
    'airline': 'G',
    'flight_number': 'H',
    'confirmation': 'I',
    'route': 'J',
    'stopover': 'K',
    'date_departure': 'L',
    'date_arrival': 'M',
    'time_departure': 'N',
    'time_arrival': 'O',
    'terminal': 'P',
}


def write_excel(tickets, template=None, event_location=''):
    if template:
        return write_template_excel(tickets, template, event_location)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Tickets'
    ws.row_dimensions[1].height = 20

    for col_idx, (_, header) in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font  = HEADER_FONT
        cell.fill  = HEADER_FILL
        cell.alignment = HEADER_ALIGN

    for row_idx, ticket in enumerate(tickets, 2):
        for col_idx, (key, _) in enumerate(COLUMNS, 1):
            ws.cell(row=row_idx, column=col_idx, value=ticket.get(key, ''))

    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def write_template_excel(tickets, template, event_location=''):
    wb = load_workbook(template)
    ida_ws = wb['IDA'] if 'IDA' in wb.sheetnames else wb.active
    regreso_ws = wb['Regresos'] if 'Regresos' in wb.sheetnames else ida_ws

    by_sheet = {'IDA': [], 'Regresos': []}
    for ticket in tickets:
        sheet_name = _pick_template_sheet(ticket, event_location)
        by_sheet[sheet_name].append(ticket)

    if by_sheet['IDA']:
        _append_template_rows(ida_ws, by_sheet['IDA'], max_col=18)
    if by_sheet['Regresos']:
        _append_template_rows(regreso_ws, by_sheet['Regresos'], max_col=17)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def _append_template_rows(ws, tickets, max_col):
    row = _last_data_row(ws) + 1
    style_row = _last_data_row(ws)

    for ticket in tickets:
        _copy_row_style(ws, style_row, row, max_col)
        values = _template_values(ticket)
        for key, col in TEMPLATE_COLUMNS.items():
            ws[f'{col}{row}'] = values.get(key, '')
        row += 1


def _template_values(ticket):
    return {
        'first_name': ticket.get('first_name', '').strip().upper(),
        'last_name': ticket.get('last_name', '').strip().upper(),
        'passport': ticket.get('passport', ''),
        'airline': _format_airline(ticket.get('airline', '')),
        'flight_number': ticket.get('flight_number', '').strip().upper(),
        'confirmation': ticket.get('confirmation', '').strip().upper(),
        'route': _format_route(ticket.get('route', '')),
        'stopover': ticket.get('stopover', ''),
        'date_departure': _format_date(ticket.get('date_departure', '')),
        'date_arrival': _format_date(ticket.get('date_arrival', '')),
        'time_departure': _format_time(ticket.get('time_departure', '')),
        'time_arrival': _format_time(ticket.get('time_arrival', '')),
        'terminal': ticket.get('terminal', ''),
    }


def _pick_template_sheet(ticket, event_location=''):
    route = ticket.get('route', '').upper()
    parts = [p.strip() for p in re.split(r'\s+-\s+|-', route) if p.strip()]
    event_names = _event_location_names(event_location)
    if len(parts) >= 2 and _looks_like_event_location(parts[0], event_names):
        return 'Regresos'
    if len(parts) >= 2 and _looks_like_event_location(parts[-1], event_names):
        return 'IDA'
    return 'IDA'


def _event_location_names(event_location):
    names = {part.strip().upper() for part in re.split(r'[,/;|]', event_location) if part.strip()}
    if not names:
        names = {'LIS', 'LISBOA', 'LISBON'}
    return names


def _looks_like_event_location(value, event_names):
    value = value.strip().upper()
    return any(value == name or name in value for name in event_names)


def _last_data_row(ws):
    for row in range(ws.max_row, 1, -1):
        values = [ws.cell(row=row, column=col).value for col in range(3, 16)]
        if any(value not in (None, '') for value in values):
            value_c = ws.cell(row=row, column=3).value
            if value_c not in ('WOW CONTROL VIAJES',) and not _is_header_or_section(value_c):
                return row
    return 1


def _is_header_or_section(value):
    if not isinstance(value, str):
        return False
    value = value.strip().upper()
    if value in {'PUESTO', 'PSM'}:
        return True
    return any(month in value for month in MONTHS_ES.values())


def _copy_row_style(ws, source_row, target_row, max_col):
    ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height
    for col in range(1, max_col + 1):
        source = ws.cell(row=source_row, column=col)
        target = ws.cell(row=target_row, column=col)
        if source.has_style:
            target._style = copy.copy(source._style)
        if source.number_format:
            target.number_format = source.number_format
        if source.alignment:
            target.alignment = copy.copy(source.alignment)
        if source.protection:
            target.protection = copy.copy(source.protection)


def _format_airline(value):
    value = value.strip().upper()
    return {
        'AIR EUROPA': 'AIREUROPA',
        'RENFE': 'RENFE',
    }.get(value, value)


def _format_route(value):
    value = value.strip().upper()
    return re.sub(r'\s+-\s+', '-', value)


def _format_date(value):
    value = value.strip()
    match = re.match(r'^(\d{1,2})/(\d{1,2})/\d{4}$', value)
    if not match:
        return value.upper()
    day = int(match.group(1))
    month = MONTHS_ES.get(f'{int(match.group(2)):02d}', '')
    return f'{day} DE {month}' if month else value


def _format_time(value):
    value = value.strip()
    match = re.match(r'^(\d{1,2}):(\d{2})$', value)
    if not match:
        return value.upper()
    return f'{int(match.group(1)):02d}H{match.group(2)}'
