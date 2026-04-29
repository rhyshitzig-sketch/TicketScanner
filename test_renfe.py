import io, sys, pdfplumber
sys.path.insert(0, '.')
from parsers.renfe import parse

EXPECTED = ['7192702000840', '7192702000857', '7192702000865', '7192702000873']

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'Omio_Print_Tickets_P28SJP.pdf'

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        result = parse(text)
        got      = result.get('ticket_number', '')
        expected = EXPECTED[i]
        status   = 'OK' if got == expected else 'FAIL'
        print(f'Page {i+1}: [{status}]  got={got!r}  expected={expected!r}')
        if status == 'FAIL':
            print('  --- raw lines ---')
            for ln in text.split('\n'):
                if 'Billete' in ln or 'billete' in ln:
                    print(f'  {ln!r}')
