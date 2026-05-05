import re
from . import renfe, cdv, vueling, ryanair, cp, iberia, volotea

# Order matters if layouts overlap — more-specific formats first
PARSERS = [cdv, vueling, ryanair, cp, iberia, volotea, renfe]


def _matches(parser, text):
    """Check if text belongs to this parser.
    Prefers declarative SIGNALS list (any one match wins) over detect()."""
    signals = getattr(parser, 'SIGNALS', None)
    if signals:
        return any(re.search(sig, text, re.IGNORECASE) for sig in signals)
    return parser.detect(text)


def detect_and_parse_doc(pages_text):
    """Try document-level parsers (need all pages). Returns None if none match."""
    combined = '\n'.join(t for t in pages_text if t)
    for parser in PARSERS:
        if getattr(parser, 'DOCUMENT_LEVEL', False) and _matches(parser, combined):
            result = parser.parse(combined)
            return result if isinstance(result, list) else [result]
    return None


def detect_and_parse(text):
    """Per-page parsing. Skips document-level parsers."""
    for parser in PARSERS:
        if getattr(parser, 'DOCUMENT_LEVEL', False):
            continue
        if _matches(parser, text):
            result = parser.parse(text)
            return result if isinstance(result, list) else [result]
    return []
