import os
import smtplib
import ssl
import sys

from .totals import notify_totals


def main():
    if len(sys.argv) != 1:
        print('Usage: romanesco-notify')
        sys.exit(1)

    cfg = dict(
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'localhost'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 25)),
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', os.environ.get('MAIL_PORT') == '587'),
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', os.environ.get('MAIL_PORT') == '465'),
        MAIL_TIMEOUT=os.environ.get('MAIL_TIMEOUT'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'romanesco@localhost')
    )
    if cfg['MAIL_USE_TLS'] and cfg['MAIL_USE_SSL']:
        print('Conflicting options: MAIL_USE_TLS and MAIL_USE_SSL')
        sys.exit(2)

    with smtp_connect(cfg) as smtp:
        # TODO: later we can add multiple types of notifications
        notify_totals(cfg, smtp)


def smtp_connect(cfg):
    kwargs = dict(
        host=cfg['MAIL_SERVER'], port=cfg['MAIL_PORT'],
        timeout=cfg['MAIL_TIMEOUT']
    )
    if cfg['MAIL_USE_SSL']:
        ssl_context = ssl.create_default_context()
        smtp = smtplib.SMTP_SSL(**kwargs, context=ssl_context)
    else:
        smtp = smtplib.SMTP(**kwargs)
    if cfg['MAIL_USE_TLS']:
        ssl_context = ssl.create_default_context()
        smtp.starttls(context=ssl_context)
    if cfg['MAIL_USERNAME'] is not None:
        smtp.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
    return smtp


if __name__ == '__main__':
    main()

