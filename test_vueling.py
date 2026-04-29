import sys
sys.path.insert(0, '.')
from parsers.vueling import parse

PAGE1 = """Recuerda: este email no es válido como tarjeta de embarque. El check-in estará
disponible 24 horas antes de la salida del vuelo.
Gestiona tu reserva Hacer el check-in Código de reserva: IGDMTV
RESERVA
CONFIRMADA.
Ida Jueves, 21 mayo 2026
Barcelona (España) Lisboa (Portugal)
BCN LIS
07:20h 08:30h
VY8460
Vuelta Sábado, 23 mayo 2026
Lisboa (Portugal) Barcelona (España)
LIS BCN
19:20h 22:15h
VY8465
PASAJEROS Y SERVICIOS"""

PAGE2 = """Pasajeros Ida Vuelta
Diego Alejandro Mejias Hernandez
• Asiento - -
• 1 pieza de equipaje de mano bajo el
asiento
Máx 40x30x20 cm 1 1
• 1 pieza de equipaje en el
compartimento superior
Máx 10 kg y 55x40x20 cm 1 1
Marin Paul
• Asiento - -
• 1 pieza de equipaje de mano bajo el
asiento
Máx 40x30x20 cm 1 1
• 1 pieza de equipaje en el
compartimento superior
Máx 10 kg y 55x40x20 cm 1 1
IMPORTANTE: Los datos introducidos en el momento de la compra deben
coincidir con los que figuran en el documento de identidad o pasaporte."""

COMBINED = PAGE1 + '\n' + PAGE2

EXPECTED = [
    {'flight_number': 'VY8460', 'route': 'BCN-LIS', 'time_departure': '07:20', 'time_arrival': '08:30',
     'date_departure': '21/05/2026', 'confirmation': 'IGDMTV', 'last_name': 'Hernandez', 'first_name': 'Diego Alejandro Mejias'},
    {'flight_number': 'VY8460', 'route': 'BCN-LIS', 'time_departure': '07:20', 'time_arrival': '08:30',
     'date_departure': '21/05/2026', 'confirmation': 'IGDMTV', 'last_name': 'Paul', 'first_name': 'Marin'},
    {'flight_number': 'VY8465', 'route': 'LIS-BCN', 'time_departure': '19:20', 'time_arrival': '22:15',
     'date_departure': '23/05/2026', 'confirmation': 'IGDMTV', 'last_name': 'Hernandez', 'first_name': 'Diego Alejandro Mejias'},
    {'flight_number': 'VY8465', 'route': 'LIS-BCN', 'time_departure': '19:20', 'time_arrival': '22:15',
     'date_departure': '23/05/2026', 'confirmation': 'IGDMTV', 'last_name': 'Paul', 'first_name': 'Marin'},
]

rows = parse(COMBINED)
print(f'Got {len(rows)} rows, expected {len(EXPECTED)}\n')
all_ok = True
for i, (row, ex) in enumerate(zip(rows, EXPECTED)):
    for key, val in ex.items():
        got = row.get(key, '')
        ok  = got == val
        if not ok:
            all_ok = False
        print(f'  [{i+1}] {key}: {"OK" if ok else "FAIL"}  got={got!r}  expected={val!r}')
if all_ok:
    print('\nALL PASS')
