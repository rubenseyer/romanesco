from pdfminer.layout import LAParams
from ..util import *


def parse(txt):
    lines = txt.splitlines()
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
        if '.' in lines[i+4]:
            # Normal entry
            n, ean, p, q = lines[i:i+7:2]
            items.append((n, parse_decimal(q), parse_decimal(p), ean))
            i += 10
            if n.startswith('*') and lines[i+2].startswith('-'):
                i += 4
        elif '.' in lines[i+6] and lines[i+4][0].isdigit():
            # No EAN; usually return, which is already accounted for
            i += 8
        elif '.' in lines[i+2]:
            # Special, which is already accounted for
            i += 4
        else:
            raise NotImplementedError
    i += 2
    assert sum(round(q*p) for _, q, p, _ in items) == parse_decimal(lines[i])
    return timestamp, items


def identify(txt):
    return 'ICA' in txt


def laparams():
    return LAParams(boxes_flow=None, line_margin=0)
