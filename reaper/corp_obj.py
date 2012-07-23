# encoding: utf-8

import threading
from bs4 import BeautifulSoup
import gui
from reaper import logger
from reaper.constants import HEADERS, COMMON_HEADERS
from urllib3.connectionpool import HTTPConnectionPool
import urllib2
from urllib2 import URLError
import re
import chardet

#设定错误超时，以免发生一直卡住的现象
urllib2.socket.setdefaulttimeout(30)
class CorpItem(object):
    """对抓取的单个企业数据的集合，和一些常用方法的集合"""

    _soqi_conn_pool = HTTPConnectionPool(host='www.soqi.cn', maxsize=50, block=True, headers=HEADERS)
    id_pattern = re.compile(r'id_([0-9a-zA-Z]+)\.html$')

    def __init__(self, raw_content, page_num, city_id, logger=logger):
        """构造函数
        raw_content: bs4里的对象，根节点应为<li>
        page_num: 被抓取到的页数
        city_id: 被抓去到的城市号"""
        self.page_num = page_num
        self.city_id = city_id
        # self.raw = raw_content
        self.logger = logger
        self.extracted = False

        self.extract_info(raw_content)


    @staticmethod
    def get_corp_id_and_name(li, obj=None):
        """根据<li>获取id和企业名称
        li: 根节点为<li>的bs4里的对象
        obj: 一个CorpItem对象，如果不是None，则它的id_page会被设为其在soqi.cn里的页面
        返回: 企业id和名称"""
        a = li.find_all(name='div', attrs={'class': 'resultName'})[0].h3.a

        if obj:
            obj.id_page = a.get('href')

        matches = CorpItem.id_pattern.search(a.get('href'))

        return matches.group(1).encode('utf-8') if matches else '', a.get_text().encode('utf-8')


    @staticmethod
    def get_corp_link(li, logger):
        """根据<li>获取企业主页地址
        li: 略
        返回: 企业主页地址，若没有则返回空"""
        cite = li.find_all(name='cite')[0]

        if cite.find(name='a'):
            result = ''.join(cite.a.get('href').split()).encode('utf-8')
            if not result.startswith('http://'):
                logger.warning('为%s加上了`http://\'', result)
                result = 'http://' + result
            return result
        else:
            return ''


    @staticmethod
    def get_corp_intro_and_product(soup):
        """根据企业在soqi.cn里的页面返回企业介绍和产品介绍
        soup: bs4里的对象，内容应为企业页面
        返回: 企业介绍和产品介绍（utf-8编码）"""
        extractor = lambda name: soup.find_all(
                name='h3',
                text=name.decode('utf-8')
            )[0].next_sibling.next_sibling.get_text().encode('utf-8').lstrip('	  　\n\r').rstrip('	   　\n\r')
        return extractor('公司简介'), extractor('产品及服务')


    def is_valid_item(self):
        """根据企业主页地址判断是否是合法的对象（没用主页的一律抛弃）"""
        if self.website:
            if self.website_title:
                return True

        return False


    def __getattr__(self, item):
        """因为CorpItem为部分惰性加载的原因，需要对不是惰性加载的属性做标记"""
        # if not self.extracted:
        #     self.extracted = True
        #     self.extract_info(self.raw)

        if item in ['introduction', 'product', 'website_title']:
            if self.thread.is_alive:
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
            if self.website:
                if 'hc360' in self.website or 'alibaba' in self.website:
                    return

                try:
                    if gui.misc.STOP_CLICKED:
                        return

                    request = urllib2.Request(self.website, headers=COMMON_HEADERS)
                    response = urllib2.urlopen(request)
                    self.logger.info('正在连接 %s' % self.website)
                    if response:
                        data = response.read()
                        # _matches = CorpItem.ENCODING_PATTERN.search(data)
                        # if _matches:
                        #     encoding = _matches.group(1)
                        #     self.logger.warning('%s首页检测到编码信息: %s', self._website_title, encoding)
                        #     soup = BeautifulSoup(data, 'lxml', from_encoding=encoding)
                        # else:
                        #     encoding = ''
                        #     soup = BeautifulSoup(data, 'lxml')
                        soup = BeautifulSoup(data, 'lxml')
                        title = soup.head.title.get_text()
                        # self._website_title = (title.decode(encoding) if encoding else title).encode('utf-8')
                        charset=chardet.detect(data)['encoding'].lower()
                        #解决字符编码乱码问题
                        if charset=='gbk' :
                            self._website_title=title.decode('gbk').encode('utf-8')
                        if charset=='gb2312' :
                            self._website_title=title.decode('gb2312').encode('utf-8')
                        if charset=='utf-8' or charset=='utf8':
                            self._website_title = title.encode('utf-8')
                        if (not self._website_title) or ('全球最丰富的供应信息 尽在阿里巴巴' in self._website_title):
                            return
                    else:
                        return

                    response = CorpItem._soqi_conn_pool.request('GET', self.id_page)
                    if response:
                        self._introduction, self._product = CorpItem.get_corp_intro_and_product(BeautifulSoup(response.data, 'lxml'))
                except URLError as _:
                    self.logger.warning('域名%s也许是过期了', self.website.__repr__())
                except AttributeError as _:
                    self.logger.info('%s没有标题', self.website)
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
    data = '''<li id="cur4208" class="">
<div class="resultSummary" id="info4208">
<div class="resultName">
<h3>
<input type="hidden" id="company_status4208" value="9">
<a href="http://www.soqi.cn/detail/id_1070DJUT89CB.html" target="_blank" id="company_name_4208">安徽长江机床制造(集团)有限<em><em>公司</em></em></a>
</h3>
<span class="img">
<img src="http://static.soqi.cn/images/rz.gif" id="exponent4208">
<div class="audit_div">
 	<div class="audit_content1" id="audit_4208" style="display: none; ">高新技术企业、品牌企业</div>
</div>
</span>
<div class="list_nav" id="trust_list_nav_4208" style="display: none; ">
<!-- onclick="loadNacaoCompany('4208',false,false,true);return false;" -->
		<a href="http://tool.soqi.cn/toolsDetail/1070DJUT89CB" title="点击查看工商档案" target="_blank" class="cleck c_1"></a>
	</div>
</div>
<div class="l_r">
<div class="l_r_mes">
	<p style="color: #999">产品服务:
    		主营产品或服务： 液压摆式剪板机,数控折弯机,三（四）辊卷板...
    			</p>
    <ul>
  <!--
  	<li>联系人:
	邰召福 经理</li>
	<li>电话:555-6061888-6061353</li>
    <li>传真:0555-6765932</li>
    <li>
    	手机:13865606360</li>
    <li>邮箱:<a style="margin: 0" href="mailto:466930138@qq.com">466930138@qq.com</a></li>
 	<li class="qq">Q Q:
	<a href="tencent://message/?uin=466930138&amp;Site=www.soqi.cn&amp;Menu=yes">466930138</a>
	</li>
	-->

 	<li>
		<span title="当涂县当涂博望镇西工业园">地址:
		当涂县当涂博望镇西工业园(243132)</span>
 	 </li>
 	</ul>
  </div>
  <div style="clear:both"></div>

  	<cite>
		收录:2012-05-13<a href="http://ahxny.b2b.hc360.com" target="_blank">
				http://ahxny.b2b.hc360.com</a>
		</cite>
  </div>
</div>
<div class="h24" id="h244208" style="display: block; ">&nbsp;</div>
<div class="list" id="list4208" style="display: none; ">
<span class="relative" id="span_copy_info_4208">
	<a href="#" onclick="copyToClipboard(4208);buttionClick('13');return false;">复制</a>
</span>
<span class="relative" id="importcrm1070DJUT89CB">
<a href='javascript:AddToCRM("1070DJUT89CB")' onclick="buttionClick('9');">导入SoQiCRM</a>
	</span>
<span class="relative" id="correct_a4208">
	<a href="javascript:loadWindow('','报错','4208')" onclick="buttionClick('11');">报错</a>
</span>
<span id="correct_span4208" style="display: none;" class="gray">报错</span>
<!--
<div class="l_ts" id="l_ts4208">
<div class="l_point_div8" id="report_point4208">
<p style="float:left">举报并纠正错误，可获得积分兑换礼品。</p>
<div class="box_close2" onclick="closeErrorInfo()" style="cursor: pointer;" id="report_box_close4208">
	<img onmouseover="this.src='http://static.soqi.cn/images/l_close.gif'" onmouseout="this.src='http://static.soqi.cn/images/l_close_gray.gif'" src="http://static.soqi.cn/images/l_close_gray.gif" />
</div>
</div>
</div>
 -->
</div>
<div class="clear"></div>
</li>'''

    dd = '''<li id="cur4266" class="cur">
<div class="resultSummary" id="info4266">
<div class="resultName">
<h3>
<input type="hidden" id="company_status4266" value="1">
<a href="http://www.soqi.cn/detail/id_10AAKTNWVPO3.html" target="_blank" id="company_name_4266">北京<em><em>太阳</em></em><em><em>帆</em></em>科技开发公司</a>
</h3>
<span class="img">
<img src="http://static.soqi.cn/images/rz.gif" id="exponent4266">
<div class="audit_div">
 	<div class="audit_content1" id="audit_4266" style="display: none; ">高新技术企业</div>
</div>
</span>
<div class="list_nav" id="trust_list_nav_4266" style="display: block; ">
<!-- onclick="loadNacaoCompany('4266',false,false,true);return false;" -->
		<a href="http://tool.soqi.cn/toolsDetail/10AAKTNWVPO3" title="点击查看工商档案" target="_blank" class="cleck c_1"></a>
	</div>
</div>
<div class="l_r">
<div class="l_r_mes">
	<p style="color: #999">产品服务:
    		太阳能及电热产品</p>
    <ul>
  <!--
  	<li>联系人:
	盛晓宏</li>
	<li>电话:010-65780107 </li>
    <li>传真:010-65780109</li>
    <li>邮箱:<a style="margin: 0" href="mailto:mdwk@263.net">mdwk@263.net</a></li>
 	-->

 	<li>
		<span title="北京市朝阳区马各庄北工业园">地址:
		北京市朝阳区马各庄北工业园(100024)</span>
 	 </li>
 	</ul>
  </div>
  <div style="clear:both"></div>

  	<cite>
		收录:2010-01-01<a href="http://www.solar-sail.com" target="_blank">
				http://www.solar-sail.com</a>
		</cite>
  </div>
</div>
<div class="h24" id="h244266" style="display: none; ">&nbsp;</div>
<div class="list" id="list4266" style="display: block; ">
<span class="relative" id="span_copy_info_4266">
	<a href="#" onclick="copyToClipboard(4266);buttionClick('13');return false;">复制</a>
</span>
<span class="relative" id="importcrm10AAKTNWVPO3">
<a href='javascript:AddToCRM("10AAKTNWVPO3")' onclick="buttionClick('9');">导入SoQiCRM</a>
	</span>
<span class="relative" id="correct_a4266">
	<a href="javascript:loadWindow('','报错','4266')" onclick="buttionClick('11');">报错</a>
</span>
<span id="correct_span4266" style="display: none;" class="gray">报错</span>
<!--
<div class="l_ts" id="l_ts4266">
<div class="l_point_div8" id="report_point4266">
<p style="float:left">举报并纠正错误，可获得积分兑换礼品。</p>
<div class="box_close2" onclick="closeErrorInfo()" style="cursor: pointer;" id="report_box_close4266">
	<img onmouseover="this.src='http://static.soqi.cn/images/l_close.gif'" onmouseout="this.src='http://static.soqi.cn/images/l_close_gray.gif'" src="http://static.soqi.cn/images/l_close_gray.gif" />
</div>
</div>
</div>
 -->
</div>
<div class="clear"></div>
</li>'''
    ppp = '''<li id="cur4226" class="cur">
<div class="resultSummary" id="info4226">
<div class="resultName">
<h3>
<input type="hidden" id="company_status4226" value="1">
<a href="http://www.soqi.cn/detail/id_1082EMBG0Z2T.html" target="_blank" id="company_name_4226"><em><em>巴</em></em><em><em>克</em></em><em><em>约</em></em><em><em>根</em></em><em><em>森</em></em>风机(宁波)有限公司</a>
</h3>
<span class="img">
<div class="audit_div">
 	<div class="audit_content1" id="audit_4226" style="display:none;"></div>
</div>
</span>
<div class="list_nav" id="trust_list_nav_4226" style="display: block; ">
<!-- onclick="loadNacaoCompany('4226',false,false,true);return false;" -->
		<a href="http://tool.soqi.cn/toolsDetail/1082EMBG0Z2T" title="点击查看工商档案" target="_blank" class="cleck c_1"></a>
	</div>
</div>
<div class="l_r">
<div class="l_r_mes">
	<p style="color: #999">产品服务:
    		风机,离心风机,鼓风机,引风机,锅炉风机,进口风机,通风机,...
    			</p>
    <ul>
  <!--
  	<li>联系人:
	Jan&#x20;Berg</li>
	<li>电话:0574-86306780</li>
    <li>传真:0574-86306782</li>
    <li>
    	手机:13738464168</li>
    -->

 	<li>
		<span title="浙江宁波市镇海区北欧工业园区金川路66号">地址:
		浙江宁波市镇海区北欧工业园区金川路66号(315221)</span>
 	 </li>
 	</ul>
  </div>
  <div style="clear:both"></div>

  	<cite>
		收录:2010-01-01<a href="http://www.nbbarker.com.cn" target="_blank">
				http://www.nbbarker.com.cn</a>
		</cite>
  </div>
</div>
<div class="h24" id="h244226" style="display: none; ">&nbsp;</div>
<div class="list" id="list4226" style="">
<span class="relative" id="span_copy_info_4226">
	<a href="#" onclick="copyToClipboard(4226);buttionClick('13');return false;">复制</a>
</span>
<span class="relative" id="importcrm1082EMBG0Z2T">
<a href='javascript:AddToCRM("1082EMBG0Z2T")' onclick="buttionClick('9');">导入SoQiCRM</a>
	</span>
<span class="relative" id="correct_a4226">
	<a href="javascript:loadWindow('','报错','4226')" onclick="buttionClick('11');">报错</a>
</span>
<span id="correct_span4226" style="display: none;" class="gray">报错</span>
<!--
<div class="l_ts" id="l_ts4226">
<div class="l_point_div8" id="report_point4226">
<p style="float:left">举报并纠正错误，可获得积分兑换礼品。</p>
<div class="box_close2" onclick="closeErrorInfo()" style="cursor: pointer;" id="report_box_close4226">
	<img onmouseover="this.src='http://static.soqi.cn/images/l_close.gif'" onmouseout="this.src='http://static.soqi.cn/images/l_close_gray.gif'" src="http://static.soqi.cn/images/l_close_gray.gif" />
</div>
</div>
</div>
 -->
</div>
<div class="clear"></div>
</li>'''
    soup = BeautifulSoup(dd)

    item = CorpItem(soup, 2, '100000')

    if item.is_valid_item():
        print 'w', item.website_title
        print 'i', item.introduction
        print 'p', item.product

