import warnings
from pdfminer.layout import LAParams
from . import ReceiptParseWarning
from ...util import *


def parse(txt):
    lines = txt.splitlines()

    comment = lines[2]
    i = 0
    while not lines[i].startswith('Datum'):
        i += 1
    i += 2
    ymd = lines[i]
    while not lines[i].startswith('Tid'):
        i += 1
    i += 2
    hm = lines[i]
    timestamp = ymdhm_to_dt(ymd, hm)

    while not lines[i].startswith('Summa'):
        i += 1
    i += 2
    # Start of items
    items = []
    while True:
        # Forward until EAN (fully numerical str).
        while not (lines[i].isdigit() and len(lines[i]) >= 8) and not lines[i].startswith('Total:'):
            i += 1
        if lines[i].startswith('Total:'):
            break
        n, ean, p, q = lines[i-2:i+5:2]
        i += 5  # Shortcut no longer safe
        items.append((n.lstrip('* '), parse_decimal(q), parse_decimal(p), ean))
    i += 2

    parsed_total = sum(round(q*p) for _, q, p, _ in items)
    total = parse_decimal(lines[i])
    if parsed_total != total:
        # Sadly we lost the ability to parse out discounts
        warnings.warn(ReceiptParseWarning(f'Parsed total does not match actual total: got {parsed_total}, expected {total}'))

    return timestamp, comment, items


def identify(txt):
    return 'ICA' in txt


def laparams():
    return LAParams(boxes_flow=None, line_margin=0, char_margin=0.2)
