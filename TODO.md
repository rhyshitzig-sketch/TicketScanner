# TODO

## Carriers to add
Each carrier needs a sample PDF run through debug.html first to map the real pdfplumber layout.

- [ ] TAP Air Portugal — need sample PDF
- [ ] Air Europa — need sample PDF

## Features
- [ ] Append to an existing Excel file instead of always generating a new one
- [ ] Show a per-row confidence indicator when a field was guessed vs clearly matched
- [ ] Support dragging in a whole folder at once (currently requires selecting files individually)
- [ ] Handle multi-passenger PDFs (multiple tickets per page, not just per file)
- [ ] Carrier auto-detection feedback in the UI (show which parser matched each file)

## Known limitations
- Renfe names are abbreviated (e.g. `R.HITZIG-S.`) — full names must be filled in manually
- OCR not supported; purely text-based PDFs only
- No de-duplication if the same PDF is uploaded twice

## Done
- [x] Renfe parser (outbound + return, multi-page bundles)
- [x] Ryanair, Vueling, CP, Iberia, Volotea, KLM, Iryo parsers
- [x] easyJet parser (per-page boarding pass, Spanish)
- [x] LATAM parser (document-level, two flights per page, cross-midnight arrivals)
- [x] Editable results table with per-cell editing before export
- [x] Excel export with styled header row
- [x] Debug tool at `/debug.html` for mapping new carrier layouts
- [x] Per-page processing (handles both single-ticket and multi-ticket PDFs)
