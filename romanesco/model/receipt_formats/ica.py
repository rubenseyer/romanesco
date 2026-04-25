import decimal
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
        # Forward until EAN
        if lines[i].startswith('Betalat') or lines[i].startswith('Total:'):
            break
        elif lines[i].isdigit() and len(lines[i]) >= 7:
            # EAN detected (fully numerical str of sufficient length), register a line
            # (Actually, new receipts seem to use internal numbers and not EANs anymore...)
            n, ean, p, q = lines[i-2:i+5:2]
            n, ean, p, q = n.lstrip('* '), ean, parse_decimal(p), parse_decimal(q)
            # Try to find a total
            try:
                tot = parse_decimal(lines[i+6])
                # Discounts are not included. Try to update it below
                if lines[i-2].startswith('*'):
                    j = i-2
                    # we have to go backwards to find the total number of contiguous discount items
                    while j >= 10 and lines[j-10].startswith('*'):
                        j -= 10
                    # then go forwards to find the discount:
                    total_discount_lines = 1
                    while lines[j + 10].startswith('*'):
                        j += 10
                        total_discount_lines += 1
                    #print(n, total_discount_lines)
                    if lines[j+12].startswith('-'):
                        # Probably a discount on the previous line
                        tot -= parse_decimal(lines[j+12][1:]) / total_discount_lines
            except decimal.InvalidOperation:
                tot = None
            if tot is not None and tot != round(q * p):
                newq = round(tot/p, Decimal("0.001"))
                # Try to explain the mismatch.
                if lines[i+8] == 'Pant':  # Deposit charge, adjust total(!)
                    tot += parse_decimal(lines[i+14])
                elif lines[i+4].endswith('kg'):  # Weight-based item, accept the new quantity
                    q = newq
                elif tot != round(q * p):  # Give up
                    warnings.warn(ReceiptParseWarning(f'Item {n} parsed total mismatch: got {round(q * p)}, expected {tot}. Should the quantity be {newq} or is there pant?'))
            i += 5  # Shortcut no longer safe
            items.append((n, q, p, ean))
        else:
            i += 1
    i += 2

    parsed_total = sum(round(q*p) for _, q, p, _ in items)
    total = parse_decimal(lines[i])
    if parsed_total != total:
        warnings.warn(ReceiptParseWarning(f'Parsed total does not match actual total: got {parsed_total}, expected {total}'))

    return timestamp, comment, items


def identify(txt):
    return 'ICA' in txt


def laparams():
    return LAParams(boxes_flow=None, line_margin=0, char_margin=0.2)
