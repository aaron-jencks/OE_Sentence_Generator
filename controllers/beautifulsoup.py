import urllib.request as request
from urllib.error import HTTPError
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Union, List, Dict, Tuple
from tqdm import tqdm
import re
import math
import os.path as path
import os

from controllers.ui import error, debug
from soup_targets import wiktionary_root
from settings import cache_html, offline_mode, html_cache_path
from utils.web import prepare_filename


def simple_get(url: str) -> bytes:
    fname = prepare_filename(url)
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


def table_parsing(table: BeautifulSoup, parsings: List[Tuple[str, int, int]]) -> Dict[str, str]:
    result = {}
    rows = table.find_all('tr')
    for name, row, col in parsings:
        if row < len(rows):
            r = rows[row]
            columns = r.findAll(['th', 'td'])
            if col < len(columns):
                result[name] = columns[col].text.strip()
            else:
                debug('Index {} doesn\'t exist in row {} for table with {} columns'.format(col, name, len(columns)))
        else:
            debug('Index {} doesn\'t fit inside a table with {} rows'.format(row, len(rows)))
    return result


class OEScraper:
    def __init__(self, url: str, all_pages: bool = True, initial_table_set: set = None):
        self.url = url
        self.soup: Union[None, BeautifulSoup] = None
        self.word_list: List[str] = []
        self.table_set = set() if initial_table_set is None else initial_table_set
        self.all_pages = all_pages
        self.setup()

    def setup(self):
        resp = simple_get(self.url)
        if resp is not None:
            self.soup = BeautifulSoup(resp, 'html.parser')

    @staticmethod
    def parse_table(table: BeautifulSoup, parsings: List[Tuple[str, int, int]]) -> Dict[str, str]:
        result = {}
        rows = table.find_all('tr')
        for name, row, col in parsings:
            if row < len(rows):
                r = rows[row]
                columns = r.findAll(['th', 'td'])
                if col < len(columns):
                    result[name] = columns[col].text.strip()
                else:
                    debug('Index {} doesn\'t exist in row {} for table with {} columns'.format(col, name, len(columns)))
            else:
                debug('Index {} doesn\'t fit inside a table with {} rows'.format(row, len(rows)))
        return result

    @staticmethod
    def find_element_items(soup: BeautifulSoup) -> List[BeautifulSoup]:
        header = soup.find('h2', text=re.compile(r'Pages in category.*'))
        if header is not None:
            lis = header.find_all_next('lis')
            footer = soup.find('div', attrs={'id': 'catlinks'})
            if footer is not None:
                footer_li = footer.find('li')
                if footer_li is not None:
                    new_lis = []
                    for li in lis:
                        if li.text == footer_li.text:
                            break
                        else:
                            new_lis.append(li)
                    lis = new_lis
            else:
                debug('page had no category links')
            return lis
        else:
            debug('page had no elements')
        return []

    def get_paqe_count(self) -> int:
        if self.soup is not None:
            pages = self.soup.find('div', attrs={'id': 'mw-pages'})
            pages = pages.find_next('p')
            page_count = re.match(r'The following (?P<current>\d+) pages are in this category, '
                                  r'out of (?P<total>\d*,?\d+) total\.', pages.text)

            total_count = int(page_count['total'].replace(',', '')) if page_count is not None else 1
            tpc = math.ceil(total_count / 200) if page_count is not None else 1
            debug('Found {} words over {} pages'.format(page_count['total'] if page_count is not None else 1, tpc))
            return tpc
        debug('{} did not have a page count entry'.format(self.url))
        return -1

    def parse_page(self, word: str, page_url: str) -> Union[List[Dict[str, str]], None]:
        pass

    def find_words(self):
        if self.soup is not None:
            tpc = self.get_paqe_count()

            self.word_list = []
            page_soup = self.soup
            for p in range(tpc if self.all_pages else 1):
                next_link = page_soup.find('a', text='next page')
                if next_link is not None:
                    next_url = wiktionary_root + '/' + next_link['href']
                else:
                    next_url = None

                lis = self.find_element_items(page_soup)
                for li in tqdm(lis, desc='Page {}'.format(p + 1)):
                    link = li.find('a').get('href')
                    page = wiktionary_root + '/' + link
                    declensions = self.parse_page(li.text, page)
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


class OEWordScraper(OEScraper):
    def __init__(self, url: str, pos_regex: str, all_pages: bool = True, initial_table_set: set = None):
        super().__init__(url, all_pages, initial_table_set)
        self.pos_regex = re.compile(pos_regex)

    def parse_definitions(self, soup: BeautifulSoup,
                          starting_dict: Dict[str, Union[str, List[str]]]) -> Union[Tag, NavigableString, None]:
        header = soup.find('span', attrs={'id': 'Old_English'})

        if header is not None:
            definitions = [d.text.split(':')[0] for d in header.find_next('ol').find_all('li')]
            starting_dict['definitions'] = definitions

            header = header.find_next('span', attrs={'id': self.pos_regex})
            return header
        return None

    def parse_forms(self, soup: BeautifulSoup, form_dict: Dict[str, Union[str, List[str]]]):
        pass

    def parse_page(self, word: str, url: str) -> Union[List[Dict[str, str]], None]:
        declensions = []
        resp = simple_get(url)
        if resp is not None:
            decls = {'word': word}
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = self.parse_definitions(w_soup, decls)

            if header is not None:
                header = header.find_next('span', attrs={'id': re.compile('(Declension|Inflection).*')})

                if header is not None:
                    tables = [tbl for tbl in header.find_all_next('div', attrs={'class': 'NavHead'})]
                    for tbl in tables:
                        if tbl.text not in self.table_set:
                            self.table_set.add(tbl.text)
                            tbl_tag = tbl.find_next('table')
                            if tbl_tag is not None:
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
                            else:
                                debug('{} had no declension table'.format(word))
                    return declensions
                else:
                    debug('{} has no declensions.'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None


class SoupStemScraper(OEScraper):
    def __init__(self, url: str, stem_type: str, all_pages: bool = True, initial_table_set: set = None):
        super().__init__(url, all_pages, initial_table_set)
        self.stem = stem_type

    def parse_page(self, word: str, url: str) -> Union[List[Dict[str, str]], None]:
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
                                if tbl_tag is not None:
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
                                else:
                                    debug('{} had no declension table'.format(word))
                        return declensions
                    else:
                        debug('{} has no declensions.'.format(word))
                else:
                    debug('{} is not a noun'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None


class SoupVerbClassScraper(SoupStemScraper):

    table_parsing_key = [
        ('infinitive can', 0, 1),
        ('infinitive to', 0, 2),
        ('indicative first singular present', 2, 1),
        ('indicative first singular past', 2, 2),
        ('indicative second singular present', 3, 1),
        ('indicative second singular past', 3, 2),
        ('indicative third singular present', 4, 1),
        ('indicative third singular past', 4, 2),
        ('indicative plural present', 5, 1),
        ('indicative plural past', 5, 2),
        ('subjunctive singular present', 7, 1),
        ('subjunctive singular past', 7, 2),
        ('subjunctive plural present', 8, 1),
        ('subjunctive plural past', 8, 2),
        ('imperative singular', 9, 1),
        ('imperative plural', 10, 1),
        ('present participle', 12, 1),
        ('past participle', 12, 2)
    ]

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

    def parse_page(self, word: str, url: str) -> Union[List[Dict[str, str]], None]:
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

                        next_span = header.find_next('span', attrs={'class': 'mw-headline'})
                        if next_span is not None:
                            spans_table = next_span.find_next('div', attrs={'class': 'NavHead'})
                            if spans_table is not None:
                                new_tables = []
                                for tbl in tables:
                                    if tbl.text == spans_table.text:
                                        break
                                    else:
                                        new_tables.append(tbl)
                                tables = new_tables

                        for tbl in tables:
                            if tbl.text not in self.table_set:
                                self.table_set.add(tbl.text)
                                tbl_tag = tbl.find_next('table')

                                data_dict = table_parsing(tbl_tag, self.table_parsing_key)
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


class SoupHeaderScraper(OEWordScraper):
    def parse_page(self, word: str, url: str) -> Union[List[str], None]:
        resp = simple_get(url)
        if resp is not None:
            conjs = []
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = self.parse_definitions(w_soup, {})

            if header is not None:
                header = header.find_next('span', attrs={'id': re.compile('(Conjugation|Declension|Inflection).*')})

                if header is not None:
                    tables = [tbl for tbl in header.find_all_next('div', attrs={'class': 'NavHead'})]

                    next_span = header.find_next('span', attrs={'class': 'mw-headline'})
                    if next_span is not None:
                        spans_table = next_span.find_next('div', attrs={'class': 'NavHead'})
                        if spans_table is not None:
                            new_tables = []
                            for tbl in tables:
                                if tbl.text == spans_table.text:
                                    break
                                else:
                                    new_tables.append(tbl)
                            tables = new_tables

                    for tbl in tables:
                        conj = ''
                        if tbl.text not in self.table_set:
                            self.table_set.add(tbl.text)
                            tbl_tag = tbl.find_next('table')
                            rows = tbl_tag.find_all('tr')
                            for ri, r in enumerate(rows):
                                data = r.findAll(['th', 'td'])
                                for element in data:
                                    if element.name == 'th':
                                        conj += element.text.replace('\n', '') + '\t'
                                    else:
                                        conj += '_\t'
                                conj += '\n'
                            conjs.append(conj)
                    return conjs if len(conjs) > 0 else None
                else:
                    debug('{} has no forms table.'.format(word))
            else:
                debug('{} is not in old english'.format(word))
        return None

    def find_words(self):
        if self.soup is not None:
            tpc = self.get_paqe_count()

            self.word_list = []
            word_set = set()
            page_soup = self.soup
            for p in range(tpc if self.all_pages else 1):
                next_link = page_soup.find('a', text='next page')
                if next_link is not None:
                    next_url = wiktionary_root + '/' + next_link['href']
                else:
                    next_url = None

                lis = self.find_element_items(page_soup)
                for li in tqdm(lis, desc='Page {}'.format(p + 1)):
                    link = li.find('a').get('href')
                    page = wiktionary_root + '/' + link
                    declensions = self.parse_page(li.text, page)
                    if declensions is not None:
                        for decl in declensions:
                            if decl not in word_set:
                                word_set.add(decl)
                                self.word_list.append((li.text, decl))
                if next_url is not None:
                    phtml = simple_get(next_url)
                    if phtml is not None:
                        page_soup = BeautifulSoup(phtml, 'html.parser')
                    else:
                        error('Failed to load the next page, finished {} of {}'.format(p + 1, tpc))
                        break

        return self.word_list


class SoupVerbHeaderScraper(SoupHeaderScraper):
    def __init__(self, url: str, all_pages: bool = True, initial_table_set: set = None):
        super().__init__(url, r'(Verb|Suffix).*', all_pages, initial_table_set)


class SoupNounHeaderScraper(SoupHeaderScraper):
    def __init__(self, url: str, all_pages: bool = True, initial_table_set: set = None):
        super().__init__(url, r'(Noun|Proper_noun|Suffix).*', all_pages, initial_table_set)


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
