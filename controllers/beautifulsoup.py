import urllib.request as request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from typing import Union, List, Dict
from tqdm import tqdm
import re
import math

from controllers.ui import error, debug
from soup_targets import wiktionary_root


def simple_get(url: str) -> str:
    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            return resp.read()
    except HTTPError as e:
        error('URL {} had an error {} {}'.format(url, e.code, e.read()))


class SoupStemScraper:
    def __init__(self, url: str, stem_type: str):
        self.url = url
        self.stem = stem_type
        self.soup: Union[None, BeautifulSoup] = None
        self.word_list: List[str] = []
        self.setup()
        self.find_words()

    def setup(self):
        resp = simple_get(self.url)
        if resp is not None:
            self.soup = BeautifulSoup(resp, 'html.parser')

    @staticmethod
    def lookup_word_declensions(word: str, url: str) -> Union[Dict[str, str], None]:
        resp = simple_get(url)
        if resp is not None:
            declensions = {'word': word}
            w_soup = BeautifulSoup(resp, 'html.parser')

            header = w_soup.find('span', attrs={'id': 'Old_English'})
            
            if header is not None:
                header = header.find_next('span', attrs={'id': 'Noun'})

                if header is not None:
                    header = header.find_next('span', attrs={'id': 'Declension'})

                    if header is not None:
                        rows = header.findAll('tr')
                        order = map(str.upper, [r.text for r in rows[0].findAll('th')])
                        for r in rows[1:]:
                            data = r.findAll(['th', 'td'])
                            data_dict = {}
                            case = ''
                            for col, d in zip(order, data):
                                data_dict[col] = d.text
                                if col == 'CASE':
                                    case = d.text
                            declensions[case] = data_dict
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

            tpc = math.ceil(int(page_count['total'].replace(',', '')) / 200)
            debug('Found {} words over {} pages'.format(page_count['total'], tpc))

            self.word_list = []
            page_soup = self.soup
            for p in range(tpc):
                next_url = wiktionary_root + '/' + page_soup.find('a', text='next page')['href']
                lis = page_soup.findAll('li', attrs={'id': ''})
                for li in tqdm(lis):
                    link = li.find('a').get('href')
                    page = wiktionary_root + '/' + link
                    declensions = self.lookup_word_declensions(li.text, page)
                    if declensions is not None:
                        self.word_list.append(declensions)
                    else:
                        debug('{} did not have any declensions'.format(li.text))
                if next_url is not None:
                    phtml = simple_get(next_url)
                    if phtml is not None:
                        page_soup = BeautifulSoup(phtml, 'html.parser')
                    else:
                        error('Failed to load the next page, finished {} of {}'.format(p + 1, tpc))
                        break


if __name__ == '__main__':
    from soup_targets import soup_targets

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
