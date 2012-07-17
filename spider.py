# encoding: utf-8

import urllib
from bs4 import BeautifulSoup
from common import dbg
from corp_obj import CorpItem


last_page_found = False

def _grab(keyword, page_number, pool, city_code='100000', predicate=None):
    """按照给定的参数进行抓取，必要时执行初步过滤
    keyword: 给定的关键字
    page_number: 页数
    pool: 所用的HTTP连接池
    city_code: 城市号
    predicate: 过滤所用的谓词"""
    global last_page_found # 最后一页的页码

    if not predicate: # 默认的谓词检测公司名是否以keyword结尾，并且CorpItem对象要有主页（不一定可用）
        predicate = lambda item: item.corp_name.endswith(keyword) and item.website

    dbg('retrieving %s of page %s' % (keyword, page_number))

    values = {
        'city': city_code,
        'keywords': keyword,
        'search_type': 0,
        'page': page_number
    }
    encoded_values = urllib.urlencode(values)

    # 出于防封考虑，使用连接池进行连接
    response = pool.request('GET', 'http://www.soqi.cn/search?' + encoded_values)

    # soqi.cn网页不标准，需要使用高级一点的解析工具
    soup = BeautifulSoup(response.data, 'lxml')

    if soup.find_all(text='上一页') and not soup.find_all(text='下一页'):
        last_page_found = page_number

    candidates = map(
        lambda raw: CorpItem(raw, page_number, city_code), # 将soup里的class为resultSummary的div转化为CorpItem对象
        filter(
            lambda x: x.has_attr('id'),
            soup.find_all(
                name='div',
                attrs={
                    'class': 'resultSummary'
                })))

    return (False if len(candidates) else True, # 可能会出现该页面非空，但是全部item都不和条件的情况
            filter(predicate, candidates))


def grab(corp_name, pool, pages, func=None):
    for page in pages:
        is_empty_page, grabbed = _grab(corp_name, page, pool)

        if func: # feeling funky lol
            for item in grabbed:
                func(item)

        yield page, is_empty_page, grabbed # 考虑到效率，提供收集完所有所需信息再写入的可能性



