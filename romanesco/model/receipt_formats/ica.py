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
        #elif 'Pant' in lines[i]:
        #    # Add bottle deposit
        #    pantp, pantq = parse_decimal(lines[i+2]), parse_decimal(lines[i+4])
        #    n, q, p, ean = items[-1]
        #    if q == pantq:
        #        items[-1] = (n, q, p + pantp, ean)
        #    else:
        #        warnings.warn(ReceiptParseWarning(f'Failed to parse pant {pantq} * {pantp}'))
        #    i += 5
        elif lines[i].isdigit() and len(lines[i]) >= 8:
            # EAN detected (fully numerical str of sufficient length), register a line
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
                #try:
                #    tot = parse_decimal(lines[i-4])
                #except decimal.InvalidOperation:
                #    tot = None
                tot = None
            if tot is not None and tot != round(q * p):
                newq = round(tot/p, Decimal("0.001"))
                warnings.warn(ReceiptParseWarning(f'Item {n} parsed total mismatch: got {round(q * p)}, expected {tot}. Should the quantity be {newq} or is there pant?'))
                # The system no longer reports quantities correctly. One heuristic is to update q if smaller than 1
                if newq < 1:
                    q = newq
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
