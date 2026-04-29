import sys
sys.path.insert(0, '.')
from parsers.cdv import parse

# Simulates pdfplumber combining columns onto one line (most likely cause of the bug)
COMBINED_COLS = """SAGRARIO VIAJES S.L.
INFORMACIÓN DE LA RESERVA
Localizador Estado Fecha de realización
7SVZNW EMITIDA 27 ABR 2026
Loc. Aerolínea: 7SVZNW
TRAYECTO 1: AEROPUERTO DE BILBAO - AEROPUERTO DE LISBOA HUMBERTO DELGADO-PORTELA
Aerolínea Salida Duración Llegada
TAP jueves 21 de mayo de 2026 1h 40m jueves 21 de mayo de 2026
Operado por PORTUGALIA BIO 12:15 LIS 12:55 T1
Vuelo TP1063 Bilbao Lisboa Humberto Delgado-Portela
TRAYECTO 2: AEROPUERTO DE LISBOA HUMBERTO DELGADO-PORTELA - AEROPUERTO DE BILBAO
Aerolínea Salida Duración Llegada
TAP sábado 23 de mayo de 2026 1h 35m sábado 23 de mayo de 2026
Operado por PORTUGALIA LIS 15:00 T1 BIO 17:35
Vuelo TP1064 Lisboa Humberto Delgado-Portela Bilbao
POLÍTICA DE EQUIPAJE, TARIFA Y BILLETES POR PASAJERO
Pasajero BIO-LIS LIS-BIO Billete
GARCIA LAMAS, JONATAN
Adulto
Economy Standard (A)
Economy Standard (U)
047 9558229050"""

# Simulates pdfplumber keeping each item on its own line
SEPARATE_LINES = """SAGRARIO VIAJES S.L.
INFORMACIÓN DE LA RESERVA
Localizador
7SVZNW
Loc. Aerolínea: 7SVZNW
Estado
EMITIDA
TRAYECTO 1: AEROPUERTO DE BILBAO - AEROPUERTO DE LISBOA HUMBERTO DELGADO-PORTELA
Aerolínea
TAP
Operado por PORTUGALIA
Vuelo TP1063
Salida
jueves 21 de mayo de 2026
BIO 12:15
Bilbao
Duración
1h 40m
Llegada
jueves 21 de mayo de 2026
LIS 12:55 T1
Lisboa Humberto Delgado-Portela
TRAYECTO 2: AEROPUERTO DE LISBOA HUMBERTO DELGADO-PORTELA - AEROPUERTO DE BILBAO
Aerolínea
TAP
Operado por PORTUGALIA
Vuelo TP1064
Salida
sábado 23 de mayo de 2026
LIS 15:00 T1
Lisboa Humberto Delgado-Portela
Duración
1h 35m
Llegada
sábado 23 de mayo de 2026
BIO 17:35
Bilbao
POLÍTICA DE EQUIPAJE, TARIFA Y BILLETES POR PASAJERO
Pasajero BIO-LIS LIS-BIO Billete
GARCIA LAMAS, JONATAN
Adulto
Economy Standard (A)
Economy Standard (U)
047 9558229050"""

EXPECTED = [
    {'flight_number': 'TP1063', 'route': 'BIO-LIS', 'time_departure': '12:15', 'time_arrival': '12:55', 'confirmation': '7SVZNW'},
    {'flight_number': 'TP1064', 'route': 'LIS-BIO', 'time_departure': '15:00', 'time_arrival': '17:35', 'confirmation': '7SVZNW'},
]

def check(label, text):
    print(f'\n=== {label} ===')
    tickets = parse(text)
    all_ok = True
    for i, (t, ex) in enumerate(zip(tickets, EXPECTED)):
        for key, val in ex.items():
            got = t.get(key, '')
            ok = got == val
            if not ok:
                all_ok = False
            print(f'  [{i+1}] {key}: {"OK" if ok else "FAIL"}  got={got!r}  expected={val!r}')
    if all_ok:
        print('  ALL PASS')

check('combined columns (likely pdfplumber output)', COMBINED_COLS)
check('separate lines', SEPARATE_LINES)
