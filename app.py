import io
import json
from pathlib import Path
import pdfplumber
from flask import Flask, request, jsonify, send_file
from parsers.router import detect_and_parse, detect_and_parse_doc
from excel_writer import write_excel

app = Flask(__name__, static_folder='static', static_url_path='')

DEFAULT_TEMPLATE_PATH = Path(
    r'\\192.168.1.4\produccion\WOW 30 - LISBOA\VIAJES\CONTROL\CONTROL VIAJES WOW 30 - LISBOA.xlsx'
)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/parse', methods=['POST'])
def parse_tickets():
    files = request.files.getlist('files')
    tickets = []
    errors  = []

    for f in files:
        try:
            raw = f.read()
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                page_texts = [p.extract_text() or '' for p in pdf.pages]

            # Document-level parsers (e.g. Vueling) get all pages concatenated
            doc_results = detect_and_parse_doc(page_texts)
            if doc_results is not None:
                for result in doc_results:
                    result['_source'] = f.filename
                    tickets.append(result)
            else:
                # Per-page fallback (Renfe, CDV, ...)
                for page_num, text in enumerate(page_texts):
                    if not text:
                        continue
                    results = detect_and_parse(text)
                    if results:
                        for result in results:
                            result['_source'] = f.filename
                            result['_page']   = page_num + 1
                            tickets.append(result)
                    else:
                        errors.append({
                            'file': f.filename,
                            'page': page_num + 1,
                            'error': 'Carrier not recognised',
                        })
        except Exception as exc:
            errors.append({'file': f.filename, 'page': None, 'error': str(exc)})

    return jsonify({'tickets': tickets, 'errors': errors})


@app.route('/debug-text', methods=['POST'])
def debug_text():
    """Returns raw pdfplumber text per page — use to diagnose parser issues."""
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'no file'}), 400
    pages = []
    with pdfplumber.open(io.BytesIO(f.read())) as pdf:
        for i, page in enumerate(pdf.pages):
            pages.append({'page': i + 1, 'text': page.extract_text() or ''})
    return jsonify(pages)


@app.route('/export', methods=['POST'])
def export_excel():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        tickets = request.form.get('tickets', '[]')
        template = request.files.get('template')
        event_location = request.form.get('event_location', '')
        tickets = json.loads(tickets)
        output = write_excel(tickets, _export_template(template), event_location)
    else:
        tickets = request.json.get('tickets', [])
        event_location = request.json.get('event_location', '')
        output = write_excel(tickets, _export_template(), event_location=event_location)

    return send_file(
        output,
        as_attachment=True,
        download_name='tickets.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


def _export_template(uploaded_template=None):
    if uploaded_template and uploaded_template.filename:
        return uploaded_template
    if DEFAULT_TEMPLATE_PATH.exists():
        return DEFAULT_TEMPLATE_PATH
    return None


if __name__ == '__main__':
    app.run(debug=True, port=5001)
