from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from datetime import datetime


def parse_decimal(s: str) -> Decimal:
    return Decimal(s.strip('abcdefghijklmnopqrstuvwxyz/ ').replace(',', '.'))


def round(d: Decimal, prec=Decimal('0.01')) -> Decimal:
    return d.quantize(prec, ROUND_HALF_UP)


def round_even(d: Decimal, prec=Decimal('0.01')) -> Decimal:
    return d.quantize(prec, ROUND_HALF_EVEN)


def tol_div(num: Decimal, den: Decimal) -> Decimal:
    q = num / den
    zeroes = 0
    q_prime = 0
    while round(q_prime * den) != num:
        zeroes += 1
        q_prime = round(q, prec=Decimal(f'0.{zeroes * "0"}1'))
    return q_prime


def ymdhm_to_dt(ymd, hm) -> datetime:
    year, month, day = (int(part) for part in ymd.split('-'))
    hour, minute = (int(part) for part in hm.split(':'))
    return datetime(year, month, day, hour, minute)


def splits_from_str(split_str: str) -> tuple[int, ...]:
    return tuple(int(s) for s in split_str.split(',')) if split_str else ()
