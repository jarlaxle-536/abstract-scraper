from .models import *
from celery.decorators import periodic_task
from celery import shared_task
from bs4 import BeautifulSoup
import requests

from .models import *
from abstract_scraper.celery import *
from celery.schedules import crontab

@shared_task
def update_proxies():
    print('updating proxies')
    proxies = scrape_proxies()
    present_proxies = [(p.ip_address, p.port) for p in Proxy.objects.all()]
    new_proxies = [Proxy(**dct) for dct in proxies
        if (dct['ip_address'], dct['port']) not in present_proxies]
    Proxy.objects.bulk_create(new_proxies)
    print(f'{len(present_proxies)} proxies are present, created {len(new_proxies)} more.')

def scrape_proxies():
    amount = 10
    response = requests.get(FREE_PROXY_LIST_URL)
    bs_object = BeautifulSoup(response.text, 'html.parser')
    table = bs_object.find('table')
    table_keys = [el.text.lower().replace(' ', '_')
        for el in table.find('thead').find_all('th')]
    entries = [[el.text for el in el.find_all('td')]
        for el in table.find('tbody').find_all('tr')][:amount]
    proxies = [{k: v for k, v in dict(zip(table_keys, e)).items()
        if k in VALID_FIELDS} for e in entries]
    return proxies

FREE_PROXY_LIST_URL = 'https://free-proxy-list.net/'
VALID_FIELDS = [f.name for f in Proxy._meta.fields if f.name != 'id']
