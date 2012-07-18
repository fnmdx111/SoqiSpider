# encoding: utf-8
import urllib
from bs4 import BeautifulSoup
import reaper
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


def get_estimate_item_amount(keyword, city_id, pool, logger, max_retry=15):
    values = {
        'city': city_id,
        'keywords': keyword,
        'search_type': 0,
        'page': 1
    }
    encoded_value = urllib.urlencode(values)

    retry = 0


    def p(tag):
        return tag.name == 'span' and '项结果'.decode('utf-8') in tag.get_text()

    while retry < max_retry:
        response = pool.request('GET', 'http://www.soqi.cn/search?' + encoded_value)
        soup = BeautifulSoup(response.data)

        tag = soup.find(p)
        if tag:
            matches = PATTERN_ITEM_AMOUNT.search(tag.get_text().encode('utf-8'))
            if matches:
                return int(matches.group(1))
        logger.info('soqi.cn返回空网页，重试')

    return -1


if __name__ == '__main__':
    print list(take(['130100', '130200', '130300', '130400', '130500', '130600', '130700', '130800', '130900', '131000', '131100', '140100', '140200', '140300', '140400', '140500', '140600', '140700', '140800', '140900', '141000', '141100'], 5))
    print get_estimate_item_amount('公司', '110000', HTTPConnectionPool('www.soqi.cn', headers=HEADERS), logger=reaper.logger)
    print get_estimate_item_amount('厂', '120000', HTTPConnectionPool('www.soqi.cn', headers=HEADERS), logger=reaper.logger)

