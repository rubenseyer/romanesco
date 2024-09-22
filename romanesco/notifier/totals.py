from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date

from tabulate import tabulate

from .. import app, db
from ..model.statistics.update import period
from ..util import round_even


def notify_totals(cfg, smtp):
    c = db.cursor()
    users = list(c.execute('select id, name, net, email, target from users where email is not null order by id'))
    period_year, period_month = period(datetime.today())
    if period_month == 1:
        period_year, period_month = period_year - 1, 12
    else:
        period_month -= 1
    when = date(period_year, period_month, 1)

    for user_id, name, net, email, target in users:
        totals = {
            category_id: (name, total)
            for category_id, name, total in c.execute('''\
                select s.category_id, c.name, s.total from stats_total s
                left join categories c on s.category_id = c.id
                where s.user_id = ? and s.year = ? and s.month = ?
                order by s.category_id asc nulls first
                ''',
                (user_id, period_year, period_month)
            )
        }
        delta = round_even(totals[None][1] - target) if target is not None else 0

        stats_table_raw = [
            [name, round_even(total)]
            for category_id, (name, total) in totals.items() if category_id is not None
        ]

        msg = MIMEMultipart('alternative')
        plain = f'''\
Hej {name}!
        
Förra månaden spenderade du {totals[None][1]} kr.
Det är {abs(delta)} kr {"mer" if delta < 0 else "mindre"} än budget.
Ditt tillgodo är därmed {net} kr.
       
Detaljerad statistik:
{tabulate(stats_table_raw, headers=['Kategori', 'Summa'], floatfmt='.2f')}
       
\U0001F966 https://romanesco.hkg.ovh/ \
        '''
        html = f'''\
<html>
<body>
<p>Hej {name}!</p>
<p>
Förra månaden spenderade du <strong>{totals[None][1]} kr</strong>.<br>
Det är {abs(delta)} kr {"mer" if delta < 0 else "mindre"} än budget.<br>
Ditt tillgodo är därmed <strong>{net} kr</strong>.
</p>
<p>
Detaljerad statistik:
{tabulate(stats_table_raw, headers=['Kategori', 'Summa'], tablefmt='html', floatfmt='.2f')}
</p>   
<p>\U0001F966 <a href="https://romanesco.hkg.ovh/">Romanesco</a></p>
</body>
</html>\
        '''
        msg['Subject'] = f'\U0001F966 Romanesco {when.strftime("%b")}: {round_even(totals[None][1])} kr'  # Put total in subject
        msg['From'] = cfg['MAIL_DEFAULT_SENDER']
        msg['To'] = email
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        smtp.send_message(msg)
    print(f'Sent {len(users)} notification(s).')
