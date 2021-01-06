import re
from pdfminer.layout import LAParams
from ..util import *


def parse(txt: str) -> (datetime, list[(str, Decimal, Decimal, None)]):
    lines = txt.splitlines()
    i = 0
    # Advance until === separator
    while not lines[i].startswith('='):
        i += 1
    i += 1
    # Read products until next separator
    name = None
    quantity = None
    price = None
    items = []
    while lines:
        line = lines[i]
        i += 1
        # No hanging indent -> close item
        if name is not None and not line.startswith(' '):
            items.append((name, quantity, price, None))
            name = quantity = price = None
        # Stop at next === separator
        if line.startswith('='):
            break
        seg = re.split('  +', line)  # Segments by spacing
        # Unindented
        if seg[0]:
            name = seg[0]
            if len(seg) == 2:
                quantity = Decimal(1)
                price = parse_decimal(seg[1])
            elif len(seg) == 3 and '*' in seg[1]:
                quantity, price = _starexpr(seg[1])
                assert round(quantity*price) == parse_decimal(seg[2])
        # Indented
        else:
            # Promo
            if ':' in seg[1] and len(seg) == 3:
                price += parse_decimal(seg[2]) / quantity
            # Addon
            elif '+' in seg[1]:
                    if len(seg) == 4:
                        addq, addp = _starexpr(seg[2])
                        price += addp
                        assert addq == quantity
                        assert round(addq*addp) == parse_decimal(seg[3])
                    elif len(seg) == 3:
                        assert quantity == 1
                        price += parse_decimal(seg[2])
            # Quantified
            elif '*' in seg[1]:
                quantity, newp = _starexpr(seg[1])
                assert round(quantity*newp) == price if price is not None else parse_decimal(seg[2])
                price = newp
    # Read total
    while 'SEK' not in lines[i]:
        i += 1
    total = parse_decimal(lines[i].split()[1])
    # Read timestamp
    timestamp = ymdhm_to_dt(*lines[-3].split()[2:4])
    # Done
    assert sum(round(q*p) for _, q, p, _ in items) == total
    return timestamp, items


def identify(txt):
    return 'Willys' in txt


def laparams():
    return LAParams()


def _starexpr(ss: str) -> (Decimal, Decimal):
    return (parse_decimal(s) for s in ss.split('*'))
