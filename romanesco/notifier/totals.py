from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from math import floor

from tabulate import tabulate

from .. import db
from ..model.statistics.get import _avg_this_day
from ..util import round_even


def notify_totals(cfg, smtp):
    c = db.cursor()
    users = list(c.execute('select id, name, net, email from users where email is not null order by id'))
    when = datetime.today().replace(day=1) - timedelta(days=1)

    for user_id, name, net, email in users:
        totals = {
            category_id: (name, total)
            for category_id, name, total in c.execute('''\
                select s.category_id, c.name, s.total from stats_total s
                left join categories c on s.category_id = c.id
                where s.user_id = ? and s.year = ? and s.month = ?
                order by s.category_id asc nulls first
                ''',
                (user_id, when.year, when.month)
            )
        }
        total_avg_delta = round_even(totals[None][1] - _avg_this_day(c,user_id,None,when))

        stats_table_raw = [
            [name, round_even(total), _avg_this_day(c,user_id,category_id,when)]
            for category_id, (name, total) in totals.items() if category_id is not None
        ]

        msg = MIMEMultipart('alternative')
        plain = f'''\
Hej {name}!
        
Förra månaden spenderade du {totals[None][1]} kr.
Det är {abs(total_avg_delta)} kr {"mer" if total_avg_delta > 0 else "mindre"} än ditt genomsnitt.
Ditt tillgodo är därmed {net} kr.
       
Detaljerad statistik:
{tabulate(stats_table_raw, headers=['Kategori', 'Summa', 'Medel'], tablefmt='rounded_outline', floatfmt='.2f')}
       
\U0001F966 https://romanesco.hkg.ovh/ \
        '''
        html = f'''\
<html>
<body>
<p>Hej {name}!</p>
<p>
Förra månaden spenderade du <strong>{totals[None][1]} kr</strong>.<br>
Det är {abs(total_avg_delta)} kr {"mer" if total_avg_delta > 0 else "mindre"} än ditt genomsnitt.<br>
Ditt tillgodo är därmed <strong>{net} kr</strong>.
</p>
<p>
Detaljerad statistik:
{tabulate(stats_table_raw, headers=['Kategori', 'Summa', 'Medel'], tablefmt='html', floatfmt='.2f')}
</p>   
<p>\U0001F966 <a href="https://romanesco.hkg.ovh/">Romanesco</a></p>
</body>
</html>\
        '''
        msg['Subject'] = f'\U0001F966 Romanesco {when.strftime("%b")}: {floor(totals[None][1])} kr'  # Put total in subject
        msg['From'] = cfg['MAIL_DEFAULT_SENDER']
        msg['To'] = email
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        smtp.send_message(msg)
    print(f'Sent {len(users)} notification(s).')
