# encoding: utf-8

import logging
import threading
from bs4 import BeautifulSoup
import gui
from gui.thread_watcher import ThreadWatcher
from reaper import logger
from reaper.constants import HEADERS, COMMON_HEADERS
from urllib3.connectionpool import HTTPConnectionPool
import urllib2
from urllib2 import URLError
import re
import chardet

class CorpItem(object):
    """对抓取的单个企业数据的集合，和一些常用方法的集合"""

    _soqi_conn_pool = HTTPConnectionPool(host='www.soqi.cn', maxsize=50, block=True, headers=HEADERS)
    id_pattern = re.compile(r'id_([0-9a-zA-Z]+)\.html$')

    def __init__(self, raw_content, page_num, city_id, thread_watcher, logger=logger):
        """构造函数
        raw_content: bs4里的对象，根节点应为<li>
        page_num: 被抓取到的页数
        city_id: 被抓去到的城市号"""
        self.page_num = page_num
        self.city_id = city_id
        self.logger = logger
        self.thread_watcher = thread_watcher

        self.extract_info(raw_content)


    @staticmethod
    def get_corp_id_and_name(div, obj=None):
        tag_a = div.h3.a
        if not tag_a:
            return '', ''

        if obj:
            obj.id_page = tag_a.get('href')

        matches = CorpItem.id_pattern.search(tag_a.get('href'))

        return matches.group(1).encode('utf-8') if matches else '', tag_a.get_text().encode('utf-8')


    @staticmethod
    def get_corp_link(div, logger):
        tag_a = div.find(name='a', attrs={'title': u'官方网站'})
        link = tag_a.get('href') if tag_a else ''
        if link and (not link.startswith('http://')):
            logger.warning('为%s加上了`http://\'', link.encode('utf-8'))
            link = 'http://' + link
        return link


    @staticmethod
    def get_corp_intro_and_product(soup):
        """根据企业在soqi.cn里的页面返回企业介绍和产品介绍
        soup: bs4里的对象，内容应为企业页面
        返回: 企业介绍和产品介绍（utf-8编码）"""
        _ = lambda tag: tag.get_text().lstrip().rstrip() if tag else ''

        tag_div_pro_service = soup.find(name='div', attrs={'class': 'pro_service'})
        tag_div_pro_service.span.replace_with(soup.new_tag(''))
        product = _(tag_div_pro_service)

        tag_div_cont = soup.find(name='div', attrs={'class': 'content content_h'})
        intro = _(tag_div_cont.p) if tag_div_cont else ''

        tag_a = soup.find(name='a', attrs={'title': u'公司详细介绍'})
        if tag_a:
            req = urllib2.Request(tag_a.get('href'), headers=HEADERS)
            soup = BeautifulSoup(urllib2.urlopen(req).read(), 'html.parser')
            tag_div = soup.find(name='div', attrs={'class': 'content'})
            if tag_div:
                intro = tag_div.p.get_text()

        return intro.encode('utf-8'), product.encode('utf-8')


    def is_valid_item(self):
        """根据企业主页地址判断是否是合法的对象（没用主页的一律抛弃）"""
        if self.website:
            if self.website_title:
                return True
            self.logger.warning('%s denied', self.corp_name)

        return False


    def __getattr__(self, item):
        """因为CorpItem为部分惰性加载的原因，需要对不是惰性加载的属性做标记"""
        if item in ['introduction', 'product', 'website_title']:
            if self.thread.is_alive():
                self.thread.join(10)
            return self.__getattribute__('_' + item)
        else:
            return self.__getattribute__(item)


    ENCODING_PATTERN = re.compile(r'<meta\s+[^>]*?charset\s*?="?\s*?([^">]+)')

    def extract_info(self, raw_content):
        """根据raw_content抽取所需要的信息
        raw_content: 略
        返回: 无"""
        self.id_page = ''
        self.id, self.corp_name = CorpItem.get_corp_id_and_name(raw_content, self)
        self.id = self.city_id + '_' + self.id
        self.website = CorpItem.get_corp_link(raw_content, self.logger)
        self._website_title = ''
        self._product = ''
        self._introduction = ''

        def per_thread():
            """略"""
            with self.thread_watcher.register(self.corp_name.decode('utf-8') + u'线程'):
                if self.website:
                    if 'hc360' in self.website or 'alibaba' in self.website:
                        return

                    try:
                        if gui.misc.STOP_CLICKED:
                            return

                        request = urllib2.Request(self.website, headers=COMMON_HEADERS)
                        response = urllib2.urlopen(request,timeout=30)
                        self.logger.info('正在连接 %s' % self.website)


                        if response:
                            raw_file = response.read()
                            soup = BeautifulSoup(raw_file,
                                                 'html.parser',
                                                 from_encoding=chardet.detect(raw_file)['encoding'].lower())
                            title = soup.head.title.get_text().encode('utf-8')
                            if (not title) or ('阿里巴巴' in title):
                                self._website_title = title
                            else:
                                return
                        else:
                            return

                        response = CorpItem._soqi_conn_pool.request('GET', self.id_page)
                        if response:
                            self._introduction, self._product = CorpItem.get_corp_intro_and_product(BeautifulSoup(response.data, 'html.parser'))
                    except URLError as _:
                        self.logger.warning('域名%s也许是过期了', self.website.__repr__())
                    except AttributeError as _:
                        self.logger.warning('%s没有标题', self.website)
                    except ValueError as e:
                        if 'unknown url type' in e.message:
                            self.logger.error('未知的URL类型: %s', self.website if self.website else 'n/a')
                    except BaseException as e:
                        self.logger.error('未知的错误: %s', e)
                    finally:
                        pass

        # 开启抓取企业和产品简介以及企业主页标题的线程
        self.thread = threading.Thread(target=per_thread, args=())
        self.thread.start()
        # self.thread.join() # thread.join()的位置有待考虑


    def get_info_as_tuple(self):
        """将对象所存内容按tuple打包后返回，方便插入excel或mysql"""
        # self.thread.join() # 目前是惰性版本的求值方式，直到需要取值了才强行阻塞，但这样使得其他访问数据的方式变得不安全
        if self.website_title:
            return (
                self.id,
                self.corp_name,
                self.introduction,
                self.product,
                self.website,
                self.website_title
            )


    def dump(self):
        """调试用代码，无视"""
        print self.id.__repr__()
        print self.corp_name.__repr__()
        print self.introduction
        print self.product.__repr__()
        print self.website.__repr__()
        print self.website_title.__repr__()




if __name__ == '__main__':
    dd = '''<div class="itemblocks">
        <h3><a href="http://www.soqi.cn/detail/id_8233A3SSZFO6.html" target="_blank">襄樊康晨机电工程有限<em>公司</em></a></h3>

        <p class="prdct">产品服务:研制、开发、生产、销售柴油发电机组
           <!--



                    研制、开发、生产、销售柴油发电机组

            -->
        </p>
        <p>地址: 湖北省襄樊（国家）高新技术产业开发区汽车工业园12号路北(441003)</p>
        <p class="sch_a"><a href="http://tool.soqi.cn/toolsDetail/8233A3SSZFO6" title="工商档案" target="_blank" rel="nofollow">工商档案</a>












             - <a href="http://www.xfkcme.com" title="官方网站" target="_blank" rel="nofollow">官方网站</a>










        </p>
    </div>'''
    soup = BeautifulSoup(dd, 'html.parser')

    item = CorpItem(soup, 2, '100000', ThreadWatcher(None), logger=logging.getLogger(__name__))

    gui.misc.STOP_CLICKED = False
    if item.is_valid_item():
        print 'w', item.website_title
        print 'i', item.introduction
        print 'p', item.product

