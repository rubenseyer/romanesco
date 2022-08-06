from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import date, datetime
from itertools import chain
import json
import os
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet
import requests
from selenium import webdriver

from ... import app, db
from ...model import parse_receipt

if TYPE_CHECKING:
    from typing import BinaryIO, Generator, Iterator, Optional
    from selenium.webdriver.remote.webdriver import WebDriver
    from ...model import Receipt


class NeedsReauthenticationError(Exception):
    pass


class BaseAdapter(ABC):
    key = None
    reversed = False

    def __init__(self, last_id: Optional[str], last_date: date, user: str, passwd: str, cookies: dict[str,str]):
        self.last_id = last_id
        self.last_date = last_date
        self.user = user
        self.passwd = passwd
        self.cookies = cookies

    def __iter__(self) -> Iterator[Receipt]:
        g = self.iter_receipt_fps()
        try:
            # Trigger initialization by loading first
            first = next(g)
            g = chain([first], g)
        except StopIteration:
            # empty is ok
            pass
        except NeedsReauthenticationError:
            print('authenticating...')
            self.authenticate()
            g = self.iter_receipt_fps()
        l = [parse_receipt(fp) for fp in g]
        return iter(l) if not self.reversed else reversed(l)

    @abstractmethod
    def authenticate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def iter_receipt_fps(self) -> Generator[BinaryIO, None, None]:
        raise NotImplementedError


@contextmanager
def with_driver(ba: BaseAdapter) -> Generator[WebDriver, None, None]:
    options = webdriver.FirefoxOptions()
    options.add_argument('--width=1680')
    options.add_argument('--height=900')
    options.headless = True
    driver = webdriver.Firefox(options=options, service_log_path=os.devnull)
    try:
        yield driver
        ba.cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    finally:
        driver.delete_all_cookies()
        driver.quit()


@contextmanager
def with_session(ba: BaseAdapter) -> Generator[requests.Session, None, None]:
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
    })
    s.cookies.update(ba.cookies)

    with s:
        yield s

    ba.cookies = s.cookies.get_dict()


if TYPE_CHECKING:
    from typing import Union, Optional


def adapter_classes() -> dict[str,type[BaseAdapter]]:
    return {cls.key: cls for cls in BaseAdapter.__subclasses__()}


def get_adapters() -> dict[int, BaseAdapter]:
    fernet = Fernet(app.config['SECRET_KEY'])
    adapters_cls = adapter_classes()

    c = db.cursor()
    adapters = {}
    for row in c.execute('select adapter_key, last_id, last_date, user_enc, passwd_enc, cookies_json, rowid from botccoli_config'):
        last_id = row[1]
        last_date = date.fromtimestamp(row[2]) if row[2] is not None else date.today()
        user = fernet.decrypt(row[3].encode('utf-8')).decode('utf-8')
        passwd = fernet.decrypt(row[4].encode('utf-8')).decode('utf-8')
        cookies = json.loads(row[5]) if row[5] is not None else dict()
        adapters[row[6]] = adapters_cls[row[0]](last_id, last_date, user, passwd, cookies)
    return adapters


def register_adapter(
        user_id: int,
        adapter_key: str,
        last_id: Optional[str],
        last_date: Optional[Union[date, datetime, int]],
        user: str,
        passwd: str,
        cookies: Optional[dict[str,str]],
) -> None:
    fernet = Fernet(app.config['SECRET_KEY'])
    adapters_cls = adapter_classes()

    if adapter_key not in adapters_cls:
        raise ValueError(f'Unknown adapter key {adapter_key}')
    if last_date is None:
        last_date = date.today()
    last_date = last_date if isinstance(last_date, int) else int(
        datetime(year=last_date.year, month=last_date.month, day=last_date.day).timestamp())
    user = fernet.encrypt(user.encode('utf-8')).decode('utf-8')
    passwd = fernet.encrypt(passwd.encode('utf-8')).decode('utf-8')
    cookies = json.dumps(cookies) if cookies is not None else None

    c = db.cursor()
    c.execute('insert into botccoli_config (user_id, adapter_key, last_id, last_date, user_enc, passwd_enc, cookies_json) \
        values (?,?,?,?,?,?,?)', (user_id, adapter_key, last_id, last_date, user, passwd, cookies))


def save_adapter(rowid: int, ada: BaseAdapter) -> None:
    last_date = datetime(year=ada.last_date.year, month=ada.last_date.month, day=ada.last_date.day).timestamp()
    cookies = json.dumps(ada.cookies)
    c = db.cursor()
    c.execute('update botccoli_config set last_id = ?, last_date = ?, cookies_json = ? \
            where rowid = ?', (ada.last_id, last_date, cookies, rowid))


from . import willys



