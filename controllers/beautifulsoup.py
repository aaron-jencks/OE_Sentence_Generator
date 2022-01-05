import urllib.request as request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from typing import Union, List, Dict, Tuple
from tqdm import tqdm
import re
import math
import os.path as path
import os

from controllers.ui import error, debug
from soup_targets import wiktionary_root
from settings import cache_html, offline_mode, html_cache_path


def simple_get(url: str) -> bytes:
    fname = url[8:].replace('/', '.').replace(':', '') + '.html'
    fpath = path.join(html_cache_path, fname)

    if offline_mode or (path.exists(fpath) and cache_html):
        if path.exists(fpath):
            with open(fpath, 'rb') as fp:
                return fp.read()
        else:
            error('URL {} doesn\'t exist in html cache for offline mode'.format(url))

    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            html = resp.read()
            if cache_html:
                if not path.exists(html_cache_path):
                    os.makedirs(html_cache_path, exist_ok=True)

                with open(fpath, 'wb+') as fp:
                    fp.write(html)
            return html
    except HTTPError as e:
        error('URL {} had an error {} {}'.format(url, e.code, e.read()))


class SoupStemScraper:
    def __init__(self, url: str, stem_type: str, all_pages: bool = True, initial_table_set: set = None):
        self.url = url
        self.stem = stem_type
        self.soup: Union[None, BeautifulSoup] = None
        self.word_list: List[str] = []
        self.table_set = set() if initial_table_set is None else initial_table_set
        self.all_pages = all_pages
        self.setup()

    def setup(self):
        resp = simple_get(self.url)
        if resp is not None:
            self.soup = BeautifulSoup(resp, 'html.parser')

    def lookup_word_declensions(self, word: str, url: str) -> Union[List[Dict[str, str]], None]:
        declensions = []
        resp = simple_get(url)
        if resp is not None:
            decls = {'word': word}
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = w_soup.find('span', attrs={'id': 'Old_English'})
            
            if header is not None:
                definitions = [d.text.split(':')[0] for d in header.find_next('ol').find_all('li')]
                decls['definitions'] = definitions

                header = header.find_next('span', attrs={'id': re.compile('(Noun|Proper_noun|Suffix).*')})

                if header is not None:
                    header = header.find_next('span', attrs={'id': re.compile('(Declension|Inflection).*')})

                    if header is not None:
                        tables = [tbl for tbl in header.find_all_next('div', attrs={'class': 'NavHead'})]
                        for tbl in tables:
                            if tbl.text not in self.table_set:
                                self.table_set.add(tbl.text)
                                tbl_tag = tbl.find_next('table')
                                rows = tbl_tag.find_all('tr')
                                order = list(map(str.upper, [r.text[:-1] for r in rows[0].findAll('th')]))
                                for r in rows[1:]:
                                    data = r.findAll(['th', 'td'])
                                    data_dict = {}
                                    case = ''
                                    for col, d in zip(order, data):
                                        if col == 'CASE':
                                            case = d.text[:-1]
                                        else:
                                            data_dict[col] = d.text[:-1]
                                    decls[case] = data_dict
                                declensions.append(decls)
                        return declensions
                    else:
                        debug('{} has no declensions.'.format(word))
                else:
                    debug('{} is not a noun'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None

    def find_words(self):
        if self.soup is not None:
            pages = self.soup.find('div', attrs={'id': 'mw-pages'})
            pages = pages.find_next('p')
            page_count = re.match(r'The following (?P<current>\d+) pages are in this category, '
                                  r'out of (?P<total>\d*,?\d+) total\.', pages.text)

            total_count = int(page_count['total'].replace(',', '')) if page_count is not None else 1
            tpc = math.ceil(total_count / 200) if page_count is not None else 1
            debug('Found {} words over {} pages'.format(page_count['total'] if page_count is not None else 1, tpc))

            self.word_list = []
            page_soup = self.soup
            for p in range(tpc if self.all_pages else 1):
                next_link = page_soup.find('a', text='next page')
                if next_link is not None:
                    next_url = wiktionary_root + '/' + next_link['href']
                else:
                    next_url = None

                lis = page_soup.findAll('li', attrs={'id': ''})[:200 if p < (tpc - 1) else (total_count - (p * 200))]
                for li in tqdm(lis, desc='Page {}'.format(p + 1)):
                    link = li.find('a').get('href')
                    page = wiktionary_root + '/' + link
                    declensions = self.lookup_word_declensions(li.text, page)
                    if declensions is not None:
                        self.word_list += declensions
                    else:
                        debug('{} did not have any forms'.format(li.text))
                if next_url is not None:
                    phtml = simple_get(next_url)
                    if phtml is not None:
                        page_soup = BeautifulSoup(phtml, 'html.parser')
                    else:
                        error('Failed to load the next page, finished {} of {}'.format(p + 1, tpc))
                        break

        return self.word_list


class SoupVerbClassScraper(SoupStemScraper):
    @staticmethod
    def parse_tense(t: str) -> str:
        m = re.match(r'(?P<tense>(past|present))(\stense)?', t)
        if m is not None:
            return m['tense'].upper()
        debug('{} is not a valid tense string'.format(t))
        return 'NONE'

    @staticmethod
    def parse_mood(t: str) -> str:
        m = re.match(r'(?P<mood>(indicative|imperative|subjunctive|participle))(\smood)?', t)
        if m is not None:
            return m['mood'].upper()
        debug('{} is not a valid mood string'.format(t))
        return 'NONE'

    @staticmethod
    def parse_person_plurality(p: str) -> Tuple[str, str]:
        m = re.match(r'(?P<person>([1-3](st|nd|rd)|first|second|third))(\sperson)?'
                     r'(\s(?P<plurality>(singular|plural)))?', p)
        if m is not None:
            person = m['person']
            if person == '1st':
                person = 'first'
            elif person == '2nd':
                person = 'second'
            elif person == '3rd':
                person = 'third'
            plurality = m['plurality'].upper() if 'plurality' in m else 'NONE'
            return person.upper(), plurality
        debug('{} is not a valid person string'.format(p))
        return 'NONE', 'NONE'

    def lookup_word_declensions(self, word: str, url: str) -> Union[List[Dict[str, str]], None]:
        conjugations = []
        resp = simple_get(url)
        if resp is not None:
            conjs = {'word': word}
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = w_soup.find('span', attrs={'id': 'Old_English'})

            if header is not None:
                definitions = [d.text.split(':')[0] for d in header.find_next('ol').find_all('li')]
                conjs['definitions'] = definitions
                conjs['conjugations'] = []

                header = header.find_next('span', attrs={'id': re.compile('(Verb|Suffix).*')})

                if header is not None:
                    header = header.find_next('span', attrs={'id': re.compile('(Conjugation|Declension).*')})

                    if header is not None:
                        tables = [tbl for tbl in header.find_all_next('div', attrs={'class': 'NavHead'})]
                        for tbl in tables:
                            if tbl.text not in self.table_set:
                                self.table_set.add(tbl.text)
                                tbl_tag = tbl.find_next('table')

                                rows = tbl_tag.find_all('tr')
                                current_mood = ''
                                current_tense_order = []
                                for r in rows:
                                    data_dict = {}

                                    head = r.findAll('th')
                                    data = r.findAll('td')
                                    if len(head) > 1:
                                        # Found a header row
                                        m, t1, t2 = head
                                        current_mood = m.text.replace('\n', '')
                                        current_tense_order = [self.parse_tense(t1.text), self.parse_tense(t2.text)]
                                    elif len(head) == 1:
                                        # Found something with a person and plurality
                                        if head[0].text.replace('\n', '') == 'infinitive':
                                            data_dict['INFINITIVE'] = {
                                                'can': data[0].text,
                                                'to': data[1].text
                                            }
                                        else:
                                            person, plurality = self.parse_person_plurality(head[0].text)
                                            data_dict[current_mood] = {'person': person, 'plurality': plurality}
                                            if len(data) > 1:
                                                for tense, d in zip(current_tense_order, data):
                                                    data_dict[tense] = d.text
                                            elif len(data) == 1:
                                                data_dict['all tenses'] = data[0].text
                                            else:
                                                debug('{} had no data for {} {}'.format(word,
                                                                                        current_mood,
                                                                                        current_tense_order))
                                    conjs['conjugations'].append(data_dict)
                                    conjugations.append(conjs)
                        return conjugations
                    else:
                        debug('{} has no conjugations.'.format(word))
                else:
                    debug('{} is not a verb'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None


class SoupVerbHeaderScraper(SoupStemScraper):
    def lookup_word_declensions(self, word: str, url: str) -> Union[str, None]:
        resp = simple_get(url)
        if resp is not None:
            conjs = ''
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = w_soup.find('span', attrs={'id': 'Old_English'})

            if header is not None:
                header = header.find_next('span', attrs={'id': re.compile('(Verb|Suffix).*')})

                if header is not None:
                    header = header.find_next('span', attrs={'id': re.compile('(Conjugation|Declension).*')})

                    if header is not None:
                        tables = [tbl for tbl in header.find_all_next('div', attrs={'class': 'NavHead'})]
                        for tbl in tables:
                            if tbl.text not in self.table_set:
                                self.table_set.add(tbl.text)
                                tbl_tag = tbl.find_next('table')
                                rows = tbl_tag.find_all('tr')
                                for r in rows:
                                    data = r.findAll(['th', 'td'])
                                    for element in data:
                                        if element.name == 'th':
                                            conjs += element.text.replace('\n', '')
                                        else:
                                            conjs += '_'
                        return conjs
                    else:
                        debug('{} has no conjugations.'.format(word))
                else:
                    debug('{} is not a verb'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None

    def find_words(self):
        if self.soup is not None:
            pages = self.soup.find('div', attrs={'id': 'mw-pages'})
            pages = pages.find_next('p')
            page_count = re.match(r'The following (?P<current>\d+) pages are in this category, '
                                  r'out of (?P<total>\d*,?\d+) total\.', pages.text)

            total_count = int(page_count['total'].replace(',', '')) if page_count is not None else 1
            tpc = math.ceil(total_count / 200) if page_count is not None else 1
            debug('Found {} words over {} pages'.format(page_count['total'] if page_count is not None else 1, tpc))

            self.word_list = set()
            page_soup = self.soup
            for p in range(tpc if self.all_pages else 1):
                next_link = page_soup.find('a', text='next page')
                if next_link is not None:
                    next_url = wiktionary_root + '/' + next_link['href']
                else:
                    next_url = None

                lis = page_soup.findAll('li', attrs={'id': ''})[:200 if p < (tpc - 1) else (total_count - (p * 200))]
                for li in tqdm(lis, desc='Page {}'.format(p + 1)):
                    link = li.find('a').get('href')
                    page = wiktionary_root + '/' + link
                    declensions = self.lookup_word_declensions(li.text, page)
                    if declensions is not None:
                        self.word_list.add(declensions)
                    else:
                        debug('{} did not have any forms'.format(li.text))
                if next_url is not None:
                    phtml = simple_get(next_url)
                    if phtml is not None:
                        page_soup = BeautifulSoup(phtml, 'html.parser')
                    else:
                        error('Failed to load the next page, finished {} of {}'.format(p + 1, tpc))
                        break

        return self.word_list


if __name__ == '__main__':
    from soup_targets import soup_targets
    from controllers.sql import SQLController

    cont = SQLController.get_instance()
    cont.setup_tables()

    for t, u in soup_targets.items():
        words = []
        debug('Searching for {}'.format(t))
        for s, url in u.items():
            debug('Searching for {}'.format(s))
            if isinstance(url, dict):
                for g, gurl in url.items():
                    debug('Checking for {}'.format(g))
                    scraper = SoupStemScraper(wiktionary_root + '/wiki/' + gurl, s)
                    words += scraper.find_words()
            else:
                scraper = SoupStemScraper(wiktionary_root + '/wiki/' + url, s)
                words += scraper.find_words()
