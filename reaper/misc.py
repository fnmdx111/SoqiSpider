# encoding: utf-8
import urllib
from bs4 import BeautifulSoup
from reaper.constants import HEADERS, PATTERN_ITEM_AMOUNT
from urllib3.connectionpool import HTTPConnectionPool


last_page_found = 0


def partition(iterable, by=10):
    """按每by个把iterable分成若干组"""
    if not by:
        return [iterable]
    return [iterable[i * by:(i + 1) * by] for i in range(len(iterable) / by  + (1 if len(iterable) % by != 0 else 0))]


def take(iterable, by=5):
    while iterable:
        if len(iterable) < by:
            yield iterable
        else:
            yield iterable[:by]
        iterable = iterable[by:]


def get_estimate_item_amount(keyword, city_id, pool):
    values = {
        'city': city_id,
        'keywords': keyword,
        'search_type': 0,
        'page': 1
    }

    response = pool.request('GET', 'http://www.soqi.cn/search?' + urllib.urlencode(values))

    soup = BeautifulSoup(response.data)

    def p(tag):
        return tag.name == 'span' and '项结果'.decode('utf-8') in tag.get_text()

    matches = PATTERN_ITEM_AMOUNT.search(soup.find(p).get_text().encode('utf-8'))

    if matches:
        return int(matches.group(1))
    return -1



if __name__ == '__main__':
    print get_estimate_item_amount('公司', '110000', HTTPConnectionPool('www.soqi.cn', headers=HEADERS))
    print get_estimate_item_amount('厂', '120000', HTTPConnectionPool('www.soqi.cn', headers=HEADERS))

