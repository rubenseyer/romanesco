import re
from pdfminer.layout import LAParams
from ...util import *


def parse(txt: str) -> (datetime, list[(str, Decimal, Decimal, None)]):
    lines = txt.splitlines()
    comment = lines[0].strip() + ' ' + lines[1].strip()
    i = 0
    # Advance until --- separator
    while not lines[i].startswith('-'):
        i += 1
    i += 1
    # Read products until next separator
    name = None
    quantity = None
    price = None
    items = []
    while i < len(lines):
        line = lines[i]
        i += 1
        # Filter useless note
        if line.startswith('Utförsäljning'):
            continue
        # No hanging indent -> close item
        if name is not None and not line.startswith(' '):
            if quantity is None:
                quantity = Decimal(0)
            if price is None:
                price = Decimal(0)
            items.append((name, quantity, price, None))
            name = quantity = price = None
        # Skip any === separators
        if line.startswith('='):
            continue
        # Stop at next --- separator
        if line.startswith('-'):
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
            if (':' in seg[1] or seg[1].startswith('Prisnedsättning') or seg[1].startswith('Nytt pris')) and len(seg) == 3:
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
                total_price = price if price is not None else parse_decimal(seg[2])
                quantity, price = _starexpr(seg[1])
                if round(quantity*price) != total_price:
                    # rounding failed??? try to fix price, because we are working with decimal quantities
                    price = tol_div(total_price, quantity)
    # Read total
    while 'SEK' not in lines[i]:
        i += 1
    total = parse_decimal(lines[i].split()[-2])
    # Read timestamp
    # Used to be last non-empty line. Now its better to look backwards for "Kassa:"
    for line in filter(None, reversed(lines)):
        if line.startswith('Kassa:'):
            timestamp = ymdhm_to_dt(*next(filter(None, lines[::-1])).split()[2:4])
            break
    else:
        timestamp = datetime(1970, 1, 1, 00, 00)
    # Done
    assert sum(round(q*p) for _, q, p, _ in items) == total
    return timestamp, comment, items


def identify(txt):
    return 'Willys' in txt


def laparams():
    return LAParams()


def _starexpr(ss: str) -> (Decimal, Decimal):
    return (parse_decimal(s) for s in ss.split('*'))
