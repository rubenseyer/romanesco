from math import floor


def date_occurrences(then, now):
    """Calculate number of occurrences of each calendar day in range."""
    rv = {}
    full_yr_obs = max((now.year - then.year - 1), 0)  # full years observed
    short = now.year == then.year
    rb = then.month if short else 13
    lb = then.month-1 if short else 0
    for day in range(1, 29):
        # add ends of range depending on if day is inside
        rv[day] = full_yr_obs * 12 \
                + (rb - then.month) - int(day < then.day) \
                + (now.month - lb) - int(now.day < day)
    # day = 29; account for leap years in full years
    # add ends of range, skipping a month if february inside but not a leap
    rv[29] = floor(full_yr_obs * 11) \
           + (__nleap(then.year+1, now.year-1) if full_yr_obs > 0 else 0) \
           + (rb - then.month) - int(then.month <= 2 < rb and not __isleap(then.year)) - int(29 < then.day) \
           + (now.month - lb) - int(lb < 2 < now.month and not __isleap(now.year)) - int(now.day < 29)
    # day = 30; same idea but easier
    rv[30] = full_yr_obs * 11 \
           + (rb - then.month) - int(then.month <= 2 < rb) - int(30 < then.day) \
           + (now.month - lb) - int(lb < 2 < now.month) - int(now.day < 30)
    # day = 31; only 7 months of the year. intersect with range. Delete the extra now day (but then will always contain)
    rv[31] = full_yr_obs * 7 \
           + sum(__MONTHS_31[then.month-1:rb-1]) \
           + sum(__MONTHS_31[lb:now.month-1]) + int(now.day == 31)
    return rv


def __isleap(yr): return yr % 4 == 0 and (yr % 100 != 0 or yr % 400 == 0)
def __nleap(lo, hi): return (hi // 4 - hi // 100 + hi // 400) - ((lo - 1) // 4 - (lo - 1) // 100 + (lo - 1) // 400)


__MONTHS_31 = (1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1)


# def date_occurrences_loop(then, now):
#     """Calculate number of occurrences of each calendar day in range."""
#     rv = {k: 0 for k in range(1, 32)}
#     cur, now = then.date(), now.date()
#     while cur <= now:
#         rv[cur.day] += 1
#         cur += timedelta(days=1)
#     return rv
#
# def __test():
#     mindate = 1325372400
#     maxdate = 1988060400
#     a = random.randrange(mindate, maxdate)
#     b = random.randrange(mindate, maxdate)
#     if a < b:
#         f = datetime.fromtimestamp(a)
#         t = datetime.fromtimestamp(b)
#     else:
#         f = datetime.fromtimestamp(b)
#         t = datetime.fromtimestamp(a)
#     r1 = date_occurrences(f,t)
#     r2 = date_occurrences_loop(f,t)
#     if r1 != r2:
#         print(f'failed {f.date} {t.date}: got {set(r1.items()) - set(r2.items())}, expected {set(r2.items()) - set(r1.items())}')
#     return r1 == r2
