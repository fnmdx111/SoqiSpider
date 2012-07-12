# encoding: utf-8

from threading import Thread
import threading
import urllib

import time
from urllib3.connectionpool import HTTPConnectionPool
from bs4 import BeautifulSoup
from common import dbg

last_page_found = False

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11',
    'Host': 'www.soqi.cn',
    'Referer': 'http://www.soqi.cn/'
}



def _grab(corp_name, page_number, pool, city_code='100000', predicate=lambda x: get_corp_name(x).endswith('公司'.decode('utf-8')) and get_corp_link(x)):
    global last_page_found
    dbg('retrieving %s of page %s' % (corp_name, page_number))

    values = {
        'city': city_code,
        'keywords': corp_name,
        # 't': str(int(time.time() * 100)),
        'search_type': 0,
        'page': page_number
    }
    encoded_values = urllib.urlencode(values)


    response = pool.request('GET', 'http://www.soqi.cn/search?' + encoded_values)
    # response = urllib2.urlopen(urllib2.Request('http://www.soqi.cn/search?' + encoded_values, headers=headers))

    soup = BeautifulSoup(response.data, 'lxml')

    if soup.find_all(text='上一页') and not soup.find_all(text='下一页'):
        last_page_found = page_number

    return map(lambda x: (x, page_number), filter(
        lambda x: x.has_attr('id') and predicate(x),
        soup.find_all(
            name='div',
            attrs={
                'class': 'resultSummary'
            })))


def grab(corp_name, pool, pages, file_obj=None, func=None, max_amount=-1, max_retry=50):
    items = []
    last_time_length = 0
    retry = 0

    for page in pages:
        grabbed = _grab(corp_name, page, pool)

        if file_obj and func:
            with threading.Lock():
                for item in map(lambda item: (func(item[0]), item[1]), grabbed):
                    print >> file_obj, '% 8s' % item[1], item[0].encode('utf-8')

        items.extend(grabbed)
        dbg(len(items))

        if last_time_length == len(items):
            if retry < max_retry:
                dbg('at %s page, empty page found, retrying(%s)' % (page, retry))
                retry += 1
            else:
                break
        else:
            if max_amount > 0:
                if len(items) > max_amount:
                    break
            retry = 0

            last_time_length = len(items)

    return items


def get_corp_name(li):
    return li.find_all(name='div', attrs={'class': 'resultName'})[0].h3.a.get_text()


def get_corp_link(li):
    cite = li.find_all(name='cite')[0]

    if cite.find(name='a'):
        return cite.a.get('href')
    else:
        return ''


def _start_multi_threading(per_thread_func, per_thread_args):
    threads = []

    for args in per_thread_args:
        threads.append(Thread(target=per_thread_func, args=args))
        threads[-1].start()

    for thread in threads:
        thread.join()


def start_multi_threading(keyword, (from_page, to_page), file_obj=None, url='www.soqi.cn', thread_num=20, max_retry=5, func=get_corp_name):
    def partition(iterable, by=10):
        if not by:
            return [iterable]
        return [iterable[i * by:(i + 1) * by] for i in range(len(iterable) / by  + (1 if len(iterable) % by != 0 else 0))]

    conn_pool = HTTPConnectionPool(host=url, maxsize=thread_num, block=True, headers=headers)

    container = []

    retry = 1

    range_all = range(from_page, to_page + 1)
    set_all = set(range_all)
    set_diff = set_all

    while set_diff:
        if retry > max_retry:
            break

        dbg('remaining %s pages: %s, retry: %s' % (len(set_diff), sorted(set_diff), retry))

        l = []
        def per_thread(*pages):
            l.extend(map(lambda item: (func(item[0]), item[1]), grab(keyword, pool=conn_pool, pages=pages, func=func, file_obj=file_obj)))

        per_thread_args = partition(list(set_diff), by=(max(set_diff) - min(set_diff)) / thread_num)

        _start_multi_threading(per_thread, per_thread_args)

        container.extend(l)

        set_diff -= set(map(lambda item: item[1], l))
        retry += 1

        if last_page_found:
            if not set(range(from_page, last_page_found + 1)) & set_diff:
                # 已经抓下来了开始页数，到最后一页的页面
                break

    return container


if __name__ == '__main__':
    with open('asb.txt', 'w') as ff:
        container = start_multi_threading("公司", (1, 30), max_retry=15, file_obj=ff, func=lambda x: get_corp_name(x) + ', ' + get_corp_link(x))

    container = sorted(container, lambda item1, item2: item1[1] - item2[1])

    with open(str(int(time.time() * 100)) + '.txt', 'w') as f:
        print >> f, len(container)
        for item in container:
            print >> f, '% 8s' % item[1], item[0].encode('utf-8')
            print '% 8s' % item[1], item[0]



