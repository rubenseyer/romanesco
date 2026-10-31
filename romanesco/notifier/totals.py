from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date

from tabulate import tabulate

from .. import app, db
from ..model.statistics.update import period
from ..model.statistics.get import recent_period_average
from ..util import round_even


def notify_totals(cfg, smtp):
    c = db.cursor()
    users = list(c.execute('select id, name, net, email from users where email is not null order by id'))
    period_year, period_month = period(datetime.today())
    if period_month == 1:
        period_year, period_month = period_year - 1, 12
    else:
        period_month -= 1
    when = date(period_year, period_month, 1)

    for user_id, name, net, email in users:
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

        average, average_periods = recent_period_average(
            user_id, datetime(period_year, period_month, 1))
        comparison = ''
        if average is not None:
            delta = round_even(totals[None][1] - average)
            periods_label = 'perioden' if average_periods == 1 else 'perioderna'
            periods_article = 'den' if average_periods == 1 else 'de'
            difference = (f'{abs(delta)} kr {"mer" if delta > 0 else "mindre"} än'
                          if delta != 0 else 'lika mycket som')
            comparison = (f'Det är {difference} snittet på {average} kr '
                          f'för {periods_article} {average_periods} föregående {periods_label}.')

        stats_table_raw = [
            [name, round_even(total)]
            for category_id, (name, total) in totals.items() if category_id is not None
        ]

        msg = MIMEMultipart('alternative')
        plain = f'''\
Hej {name}!
        
Förra perioden spenderade du {totals[None][1]} kr.
{comparison}
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
Förra perioden spenderade du <strong>{totals[None][1]} kr</strong>.<br>
{comparison + '<br>' if comparison else ''}
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
