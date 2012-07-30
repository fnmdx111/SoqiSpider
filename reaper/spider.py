# encoding: utf-8

import urllib
from bs4 import BeautifulSoup
import gui
from reaper.constants import REQUIRED_SUFFIXES
from reaper.corp_obj import CorpItem
from reaper import misc
from urllib3.exceptions import MaxRetryError

def _grab(keyword, page_number, pool, thread_watcher, city_code='100000', logger=None, predicate=None):
    """按照给定的参数进行抓取，必要时执行初步过滤
    keyword: 给定的关键字
    page_number: 页数
    pool: 所用的HTTP连接池
    city_code: 城市号
    predicate: 过滤所用的谓词
    返回: 过滤好的，所抓取的CorpItem对象列表"""
    if gui.misc.STOP_CLICKED:
        return

    if not predicate: # 默认的谓词检测公司名是否以keyword结尾，并且CorpItem对象要有主页（不一定可用）
        _p1 = lambda item: item.website and ('alibaba' not in item.website) and ('hc360' not in item.website)
        if keyword in REQUIRED_SUFFIXES:
            predicate = lambda item: _p1(item) and item.corp_name.endswith(keyword)
        else:
            predicate = lambda item: _p1(item)

    logger.info('正在获取以%s为关键字的搜索结果的第%s页' % (keyword, page_number))

    # url example: `http://www.soqi.cn/search?keywords=%E5%85%AC%E5%8F%B8&city=420600&sort=1&search_type=3&page=3'
    values = {
        'city': city_code,
        'keywords': keyword,
        'search_type': 3,
        'page': page_number,
        'sort': 1
    }
    encoded_values = urllib.urlencode(values)

    # 出于防封考虑，使用连接池进行连接
    response = pool.request('GET', 'http://www.soqi.cn/search?' + encoded_values)

    # soqi.cn网页不标准，需要使用高级一点的解析工具
    soup = BeautifulSoup(response.data, 'lxml')

    candidates = map(
        lambda raw: CorpItem(raw, page_number, city_code, logger=logger, thread_watcher=thread_watcher), # 将soup里的class为resultSummary的div转化为CorpItem对象
        soup.find_all(
            name='div',
            attrs={
                'class': 'itemblocks'
            }))

    tag_next_page = soup.find(name='span', attrs={'class': 'disabled'})
    if tag_next_page and (u'下' in tag_next_page.get_text()):
        logger.debug('last page found: %s', page_number)
        misc.last_page_found = page_number

    if len(candidates):
        logger.info('soqi.cn在第%s页返回有效信息，继续', page_number)
    else:
        logger.info('soqi.cn在第%s页返回空网页，重试', page_number)

    return (False if len(candidates) else True, # 可能会出现该页面非空，但是全部item都不和条件的情况
            filter(predicate, candidates))


def grab(keyword, pool, pages, thread_watcher, city_code='100000', logger=None, predicate=None):
    """对给定的页面列表（离散的）进行批量抓取（即调用_grab）
    抛出: 页面号，是否是空页面的变量，所抓取的CorpItem对象列表
    # 参数与_grab相同，略"""
    for page in pages:
        if gui.misc.STOP_CLICKED:
            break

        try:
            is_empty_page, grabbed = _grab(keyword,
                                           page, pool,
                                           city_code=city_code,
                                           logger=logger,
                                           predicate=predicate,
                                           thread_watcher=thread_watcher)
        except MaxRetryError:
            logger.error('urllib3 reports MaxRetryError')
            is_empty_page, grabbed = True, []

        if (not is_empty_page) and (not len(grabbed)):
            logger.info('%s非空，但是没有符合条件的结果', page)

        yield page, is_empty_page, grabbed # 考虑到效率，提供收集完所有所需信息再写入的可能性


