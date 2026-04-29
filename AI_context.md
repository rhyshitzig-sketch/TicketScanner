# Auto Ticket Filler — AI Context

## What this project does
A local web tool that accepts uploaded PDF travel tickets, extracts structured data from each one using per-carrier parsers, displays the results in an editable table, and exports to a formatted Excel file.

## Stack
- **Backend**: Python + Flask (`app.py`), runs on port 8888
- **PDF extraction**: `pdfplumber` (text-based PDFs only; no OCR)
- **Excel output**: `openpyxl`
- **Frontend**: single-page HTML/JS (`static/index.html`), no framework

## Project structure
```
app.py                  Flask server — /parse, /export, /debug-text endpoints
parsers/
  __init__.py
  renfe.py              Renfe parser (complete)
  router.py             Carrier detection + dispatch
excel_writer.py         Generates .xlsx with styled header row
static/
  index.html            Main UI — drag-drop upload, editable table, export
  debug.html            Debug tool — shows raw pdfplumber text per page
requirements.txt
start.bat               Windows one-click launcher (creates venv, installs deps)
```

## Excel column order (must match everywhere)
This order is fixed across `excel_writer.py` COLUMNS, `static/index.html` FIELDS array, and `<th>` headers:

| # | Key              | Header              |
|---|------------------|---------------------|
| 1 | last_name        | Last Name           |
| 2 | first_name       | First Name          |
| 3 | airline          | Airline             |
| 4 | flight_number    | Flight Number       |
| 5 | confirmation     | Confirmation Number |
| 6 | route            | Flight Route        |
| 7 | date_departure   | Date of Departure   |
| 8 | date_arrival     | Date of Arrival     |
| 9 | time_departure   | Time of Departure   |
|10 | time_arrival     | Time of Arrival     |

## How to add a new carrier parser
1. Create `parsers/<carrier>.py` with two functions:
   - `detect(text) -> bool` — return True if the page belongs to this carrier
   - `parse(text) -> dict` — return a dict with all 10 keys above (plus `origin`/`destination` as intermediates if useful)
2. Import it in `parsers/router.py` and add to the `PARSERS` list
3. Carrier order in PARSERS matters if layouts overlap

## Diagnosing a new carrier
Before writing a parser, always check the real pdfplumber extraction first:
- Run the app, go to `http://localhost:8888/debug.html`
- Upload the PDF — it shows the exact text and line numbers pdfplumber produces
- **Do not trust what a PDF looks like visually** — pdfplumber's line order often differs from reading order

## Renfe parser — key layout facts
The real pdfplumber extraction order (discovered via debug.html):
```
1  Localizador: P28SJP          ← confirmation; name is on the NEXT line
2  M.SANTAMAR.                  ← abbreviated name: FIRSTINITIAL.LASTNAME.
3  DNI ó DOC.ID: *****2666
4  Origen: PRINCIPE PIO 25/04/2026 11:06   ← origin + dep date + dep time, one line
5  Destino: ÁVILA 25/04/2026 12:36         ← destination + arr date + arr time, one line
6  Coche: 6 Plaza: 141 MD 18903UNICA       ← train number: TYPE + DIGITSUNICAw no space
...
```
Name format: `FIRSTINITIAL.LASTNAME.` (e.g. `R.HITZIG-S.`, `M.SANTAMAR.`) — Renfe only prints abbreviated names; full names must be edited manually.

## Per-page vs per-file tickets
Currently each PDF page is treated as one ticket. The Omio-bundled Renfe PDF has 4 pages = 4 tickets. This is intentional and handles both single-ticket files and multi-page bundles.

## Supported carriers
| Carrier      | Status    | Notes                        |
|--------------|-----------|------------------------------|
| Renfe        | Complete  | via Omio or direct           |
| Ryanair      | TODO      | need sample PDF              |
| Vueling      | TODO      | need sample PDF              |
| TAP Air      | TODO      | need sample PDF              |
| Air Europa   | TODO      | need sample PDF              |
