from abstract_scraper.celery import *
from .models import *
from asgiref.sync import sync_to_async
from celery import shared_task
from bs4 import BeautifulSoup
import requests
import asyncio
import aiohttp
import json
import faker
import time
import random

class State:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.setup()

    def setup(self):
        for attr in ['articles_to_create', 'infos_to_create']:
            setattr(self, attr, list())
        self.articles = {article.doi: article
            for article in Article.objects.all()}
        infos = Info.objects.all()
        self.infos = {info.article.doi: info for info in infos}
        self.info_dicts = {k: v.__dict__ for k, v in self.infos.items()}
        self.info_dicts = dict()
        for k, v in self.infos.items():
            self.info_dicts[k] = v.__dict__
            self.info_dicts[k]['references'] = [a.doi
                for a in v.references.all()]
        print(self.info_dicts)

    def create_all(self):
        self.create_new_articles()
        self.create_new_infos()
        self.create_new_dependencies()

    def create_new_articles(self):
        new_articles = {doi: Article(doi=doi)
            for doi in self.articles_to_create}
        Article.objects.bulk_create(new_articles.values())
        self.articles = {article.doi: article
            for article in Article.objects.all()}

    def create_new_infos(self):
        new_infos = {
            doi: Info(
                article_id=self.articles[doi].id,
                **{k: v for k, v in self.info_dicts[doi].items()
                    if k in VALID_FIELDS})
            for doi in self.infos_to_create}
        Info.objects.bulk_create(new_infos.values())
        self.infos = {info.article.doi: info for info in Info.objects.all()}

    def create_new_dependencies(self):
        for doi in self.infos_to_create:
            references = self.info_dicts[doi]['references']
            for rel_doi in references:
                self.infos[doi].references.add(self.articles[rel_doi])

@app.task
def search_outer(query, max_depth=0):
    global MAX_DEPTH
    MAX_DEPTH = max_depth
    return asyncio.run(search_many(query, MAX_DEPTH))

async def search_many(query, max_depth=0):
    global state, session, queue
    print(f'Searching results for {query} and {max_depth}.')
    state = await sync_to_async(State)()
    print(state.__dict__)
    session = aiohttp.ClientSession()
    queue = asyncio.Queue(maxsize=MAX_SIZE)
    doi = await asyncio.create_task(get_doi(query))
    queue.put_nowait((doi, ))
    result = await asyncio.create_task(scrape())
    return result

async def get_doi(query):
    doi = query
    print(f'DOI: {doi}')
    return doi

async def scrape():
    dois = list()
    async with session:
        while not queue.empty():
            print(f'Queue size: {queue.qsize()}')
            items = [await queue.get() for i in range(queue.qsize())]
            tasks = [asyncio.create_task(get_article(*item)) for item in items]
            res = await asyncio.gather(*tasks, return_exceptions=True)
            dois += [r for r in res if r]
    queue.task_done()
    await sync_to_async(state.create_all)()
    return dois

async def get_article(doi, depth=0):
    if not doi in list(state.articles) + state.articles_to_create:
        state.articles_to_create += [doi]
    if depth <= MAX_DEPTH:
        if not doi in state.infos:
            state.info_dicts[doi] = await get_info_dict(doi)
            if doi not in state.infos_to_create:
                state.infos_to_create += [doi]
        for ref in state.info_dicts[doi]['references']:
            asyncio.create_task(queue.put((ref, depth + 1)))
        return doi

async def get_info_dict(doi):
    tasks = [asyncio.create_task(func(doi))
        for func in (get_metadata, get_abstract)]
    info_dict, abstract = await asyncio.gather(*tasks)
    info_dict['abstract'] = abstract
    state.info_dicts[doi] = info_dict
    return info_dict

def get_fake_metadata(doi):
    info_dict = dict()
    info_dict['title'] = FAKER.sentence()
    info_dict['authors'] = FAKER.name()
    info_dict['references'] = [FAKER.sentence() for i in range(2)]
    return info_dict

async def get_metadata(doi):
    print(f'Getting meta for {doi}')
#    return get_fake_metadata(doi)
    info_dict = dict()
    try:
        url = API_URL.format(protocol='https', doi=doi)
        text = await fetch(session, url)
        info = json.loads(text)
        msg = info['message']
        info_dict['title'] = msg['title'][0]
        info_dict['authors'] = ', '.join(
            [f'{d["given"]} {d["family"]}' for d in msg['author']])
        info_dict['references'] = list()
        if 'reference' in msg:
            info_dict['references'] = [ref['DOI'] for ref in msg['reference']
                if 'DOI' in ref]
    except Exception as exc:
        print(f'error while getting metadata: {exc}.')
        info_dict['title'] = 'No title'
        info_dict['authors'] = 'No authors'
        info_dict['references'] = list()
    print(f'Acquired meta for {doi}')
    return info_dict

def get_fake_abstract(doi):
    return FAKER.text()

async def get_abstract(doi):
    print(f'Getting abstract for {doi}')
#    return get_fake_abstract(doi)
    url = ABSTRACT_URL.format(protocol='https', doi=doi)
    try:
        text = await fetch(session, url)
        bs_object = BeautifulSoup(text, 'html.parser')
        abstract = get_abstract_from_bs(bs_object).text
    except Exception as exc:
        print(f'error while getting abstract: {exc}.')
        abstract = 'No abstract'
    print(f'Abstract: {abstract}')
    return abstract

def get_abstract_from_bs(bs_object):
    elements = bs_object.find_all()
    els_with_abstract = [el for el in elements
        if el.text.strip().lower() == 'abstract']
    abstracts = list(map(
        lambda el: get_section_from_caption(bs_object, el),
        els_with_abstract
        ))
    abstract = sorted(abstracts, key=lambda t: len(t))[-1]
    return abstract

def get_section_from_caption(bs_object, caption_el):
    el = caption_el
    while True:
        if el.parent.text.strip() != el.text.strip(): break
        el = el.parent
    return el.nextSibling

async def fetch(session, url):
    async with session.get(url, timeout=10) as response:
        return await response.text()

VALID_FIELDS = [f.name for f in Info._meta.fields if f.name != 'id']
CROSSREF_SEARCH_URL = '{protocol}://search.crossref.org/?q={query}'
API_URL = '{protocol}://api.crossref.org/v1/works/{doi}'
ABSTRACT_URL = '{protocol}://doi.org/{doi}'

MAX_SIZE = 10
FAKER = faker.Faker('en_US')
