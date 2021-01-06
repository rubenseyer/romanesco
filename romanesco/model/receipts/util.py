from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


def parse_decimal(s: str) -> Decimal:
    return Decimal(s.strip('abcdefghijklmnopqrstuvwxyz/ ').replace(',', '.'))


def round(d: Decimal, prec=Decimal('0.01')) -> Decimal:
    return d.quantize(prec, ROUND_HALF_UP)


def ymdhm_to_dt(ymd, hm) -> datetime:
    year, month, day = (int(part) for part in ymd.split('-'))
    hour, minute = (int(part) for part in hm.split(':'))
    return datetime(year, month, day, hour, minute)
