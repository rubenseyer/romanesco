import re
import warnings
from pdfminer.layout import LAParams
from . import ReceiptParseWarning
from ...util import *


def parse(txt: str) -> tuple[datetime, str, list[tuple[str, Decimal, Decimal, None]]]:
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
    items: list[tuple[str, Decimal, Decimal, None]] = []
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
            # For some reason double-spaced items have appeared
            if len(seg) >= 3 and '*' in seg[-2]:
                name = ' '.join(seg[0:-2])
                quantity, price = _starexpr(seg[-2])
                assert round(quantity * price) == parse_decimal(seg[-1])
            elif len(seg) >= 2:
                name = ' '.join(seg[0:-1])
                quantity = Decimal(1)
                price = parse_decimal(seg[-1])
            else:
                warnings.warn(ReceiptParseWarning(f'Nonconforming item line "{line}"'))
        # Indented
        else:
            # Promo
            if (':' in seg[1] or 'Prisneds' in seg[1] or 'Nytt pris' in seg[1]) and len(seg) >= 3:
                price += parse_decimal(seg[-1]) / quantity
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
                    warnings.warn(ReceiptParseWarning(f'Entry rounding did not match: got {round(quantity*price)}, expected {total_price}'))
                    price = tol_div(total_price, quantity)
    # Read total
    while 'SEK' not in lines[i]:
        i += 1
    total = parse_decimal(lines[i].split()[-2])
    # Read timestamp
    # Used to be last non-empty line. Now its better to look backwards for "Kassa:"
    for line in filter(None, reversed(lines)):
        if line.startswith('Kassa:'):
            timestamp = ymdhm_to_dt(*line.split()[2:4])
            break
    else:
        timestamp = datetime(1970, 1, 1, 00, 00)
    # Done

    parsed_total = sum(round(q*p) for _, q, p, _ in items)
    if parsed_total != total:
        warnings.warn(ReceiptParseWarning(f'Parsed total does not match actual total: got {parsed_total}, expected {total}'))

    return timestamp, comment, items


def identify(txt):
    # Also allow hemköp!
    return 'Willys' in txt or 'Medlemsnummer' in txt


def laparams():
    return LAParams()


def _starexpr(ss: str) -> (Decimal, Decimal):
    return (parse_decimal(s) for s in ss.split('*'))


# Recently (late 2022) Willys started to send broken mappings for their receipts, which makes the files unparseable.
# This table maps back the characters so the files are machine-readable once again.
CID2UNICHR = {
    3: ' ', 4: '!', 8: '%', 9: '&', 13: '*', 14: '+', 15: ',', 16: '-', 17: '.', 18: '/',
    19: '0', 20: '1', 21: '2', 22: '3', 23: '4', 24: '5', 25: '6', 26: '7', 27: '8', 28: '9',
    29: ':', 31: '<', 32: '=', 33: '>',
    36: 'A', 37: 'B', 38: 'C', 39: 'D', 40: 'E', 41: 'F', 42: 'G', 43: 'H', 44: 'I', 45: 'J', 46: 'K', 47: 'L', 48: 'M',
    49: 'N', 50: 'O', 51: 'P', 52: 'Q', 53: 'R', 54: 'S', 55: 'T', 56: 'U', 57: 'V', 58: 'W', 59: 'X', 60: 'Y', 61: 'Z',
    67: '`',
    68: 'a', 69: 'b', 70: 'c', 71: 'd', 72: 'e', 73: 'f', 74: 'g', 75: 'h', 76: 'i', 77: 'j', 78: 'k', 79: 'l', 80: 'm',
    81: 'n', 82: 'o', 83: 'p', 84: 'q', 85: 'r', 86: 's', 87: 't', 88: 'u', 89: 'v', 90: 'w', 91: 'x', 92: 'y', 93: 'z',
    134: 'Ä', 135: 'Å', 138: 'È', 139: 'É', 152: 'Ö', 166: 'ä', 167: 'å', 184: 'ö',
    3057: '\ufffd', 34: '\ufffd'
}
