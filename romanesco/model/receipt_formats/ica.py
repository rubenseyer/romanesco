from pdfminer.layout import LAParams
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
    while not lines[i].startswith('Total:'):
        if lines[i] == 'Delavstämning korrekt' or lines[i] == 'Avstämning korrekt.':
            i += 2
        elif lines[i] == 'Stammisrabatt ICA':
            # Already accounted for in the totals.
            i += 6
        elif '.' in lines[i+4]:
            # Normal entry
            n, ean, p, q = lines[i:i+7:2]
            items.append((n.lstrip('* '), parse_decimal(q), parse_decimal(p), ean))
            i += 10
            if n.startswith('*') and lines[i+2].startswith('-') and lines[i] != 'Stammisrabatt ICA':
                i += 4
        elif '.' in lines[i+6] and lines[i+4][0].isdigit():
            # No EAN; usually return fee, which is already accounted for
            # However, return fees paid back must be added.
            if lines[i].startswith('Pantretur'):
                items.append(('Pant', Decimal(1), parse_decimal(lines[i+6]), None))
            i += 8
        elif '.' in lines[i+2]:
            # Special, which is already accounted for
            i += 4
        else:
            raise NotImplementedError
    i += 2
    assert sum(round(q*p) for _, q, p, _ in items) == parse_decimal(lines[i])
    return timestamp, comment, items


def identify(txt):
    return 'ICA' in txt


def laparams():
    return LAParams(boxes_flow=None, line_margin=0)
