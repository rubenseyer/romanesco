from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
import time
from typing import TYPE_CHECKING
import warnings

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import BaseAdapter, NeedsReauthenticationError, with_driver, with_session

if TYPE_CHECKING:
    from requests import Session
    from typing import BinaryIO, Generator
    from selenium.webdriver.remote.webdriver import WebDriver


class BaseAxfoodAdapter(BaseAdapter):
    reversed = True

    def iter_receipt_fps(self) -> Generator[BinaryIO, None, None]:
        today = date.today()
        to_date = today.strftime(AXFOOD_FDATE)
        from_date = (self.last_date if self.last_date is not None else (today - timedelta(days=14))).strftime(AXFOOD_FDATE)

        s: Session
        with with_session(self) as s:
            current_page = 0
            number_of_pages = 999
            first = True
            stop_id = self.last_id
            while current_page < number_of_pages:
                resp = s.get(self._base_url + _receipt_page(fromDate=from_date, toDate=to_date, currentPage=current_page, pageSize=10))
                if resp.status_code == 401:
                    raise NeedsReauthenticationError()
                resp.raise_for_status()
                j = resp.json()

                current_page = j['paginationData']['currentPage']
                number_of_pages = j['paginationData']['numberOfPages']
                self.logger.info(f'page: {current_page}/{number_of_pages}')
                for transact in j['loyaltyTransactionsInPage']:
                    if not transact['digitalReceiptAvailable']:
                        continue
                    cur_id = transact['digitalReceiptReference']
                    cur_date = transact['bookingDate'] = date.fromtimestamp(transact['bookingDate'] / 1000)
                    if first:  # most recent receipt is first returned
                        self.last_id = cur_id
                        self.last_date = cur_date
                        first = False
                    if cur_id == stop_id:
                        return
                    self.logger.info(cur_date, ' - ', cur_id)
                    resp = s.get(self._base_url + _receipt_pdf(**transact))
                    resp.raise_for_status()
                    yield BytesIO(resp.content)
                    time.sleep(2)
                current_page += 1


class WillysAdapter(BaseAxfoodAdapter):
    key = 'willys'
    _base_url = 'https://www.willys.se/'

    def authenticate(self) -> None:
        driver: WebDriver
        with with_driver(self) as driver:
            driver.get('https://www.willys.se/mina-kop')

            try:
                cookie_btn = WebDriverWait(driver, timeout=15).until(
                    EC.element_to_be_clickable((By.ID, 'onetrust-reject-all-handler'))
                )
                cookie_btn.click()
            except TimeoutException as e:
                warnings.warn(str(e))

            input_user = driver.find_element(By.XPATH, '//input[@name="j_username"]')
            input_pass = driver.find_element(By.XPATH, '//input[@name="j_password"]')
            submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
            input_user.send_keys(self.user)
            input_pass.send_keys(self.passwd)
            WebDriverWait(driver, timeout=15).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, 'onetrust-pc-dark-filter'))
            )
            time.sleep(2)  # Headless too fast
            submit.click()

            WebDriverWait(driver, timeout=30).until(
                EC.presence_of_element_located((By.XPATH, '//span[text()="Logga ut"]'))
            )


class HemkopAdapter(BaseAxfoodAdapter):
    key = 'hemköp'
    _base_url = 'https://www.hemkop.se/'

    def authenticate(self) -> None:
        driver: WebDriver
        with with_driver(self) as driver:
            driver.get('https://www.hemkop.se/mina-sidor/kop')

            try:
                cookie_btn = WebDriverWait(driver, timeout=15).until(
                    EC.element_to_be_clickable((By.ID, 'onetrust-reject-all-handler'))
                )
                cookie_btn.click()
            except TimeoutException as e:
                warnings.warn(str(e))

            WebDriverWait(driver, timeout=15).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, 'onetrust-pc-dark-filter'))
            )
            time.sleep(2)  # Headless too fast

            password_tab = driver.find_element(By.XPATH, '//button[contains(.,"Lösenord")]')
            password_tab.click()
            time.sleep(1)

            input_user = driver.find_element(By.XPATH, '//input[@name="j_username"]')
            input_pass = driver.find_element(By.XPATH, '//input[@name="j_password"]')
            submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
            input_user.send_keys(self.user)
            input_pass.send_keys(self.passwd)
            submit.click()

            WebDriverWait(driver, timeout=30).until(
                EC.presence_of_element_located((By.XPATH, '//p[text()="Logga ut"]'))
            )


_receipt_page = ('axfood/rest/account/pagedOrderBonusCombined'
    '?fromDate={fromDate}'
    '&toDate={toDate}'
    '&currentPage={currentPage}'
    '&pageSize={pageSize}').format

_receipt_pdf = ('axfood/rest/order/orders/digitalreceipt/{digitalReceiptReference}'
    '?date={bookingDate:%Y-%m-%d}'
    '&storeId={storeCustomerId}'
    '&source={receiptSource}'
    '&memberCardNumber={memberCardNumber}').format

AXFOOD_FDATE = '%Y-%m-%d'

