# encoding: utf-8

import threading
from common import dbg
from bs4 import BeautifulSoup
from constants import headers
from urllib3.connectionpool import HTTPConnectionPool
import urllib2
from urllib2 import URLError
import re

class CorpItem(object):

    _soqi_conn_pool = HTTPConnectionPool(host='www.soqi.cn', maxsize=50, block=True, headers=headers)
    id_pattern = re.compile(r'id_([0-9a-zA-Z]+)\.html$')

    def __init__(self, raw_content, page_num, city_id):
        self.page_num = page_num
        self.city_id = city_id

        self.extract_info(raw_content)


    @staticmethod
    def get_corp_id_and_name(li, obj=None):
        a = li.find_all(name='div', attrs={'class': 'resultName'})[0].h3.a

        if obj:
            obj.id_page = a.get('href')

        matches = CorpItem.id_pattern.search(a.get('href'))

        return matches.group(1) if matches else '', a.get_text().encode('utf-8')


    @staticmethod
    def get_corp_link(li):
        cite = li.find_all(name='cite')[0]

        if cite.find(name='a'):
            return ''.join(cite.a.get('href').split())
        else:
            return ''


    @staticmethod
    def get_corp_intro_and_product(soup):
        extractor = lambda name: ''.join(soup.find_all(name='h3', text=name.decode('utf-8'))[0].next_sibling.next_sibling.get_text().split()).encode('utf-8')

        return extractor('产品及服务'), extractor('公司简介')


    def is_valid_item(self):
        if self.website:
            return True


    def extract_info(self, raw_content):
        self.id_page = ''
        self.id, self.corp_name = CorpItem.get_corp_id_and_name(raw_content, self)
        self.id = self.city_id + '_' + self.id
        self.website = CorpItem.get_corp_link(raw_content)
        self.website_title = ''
        self.product = ''
        self.introduction = ''

        def per_thread():
            if self.website:
                try:
                    response = urllib2.urlopen(self.website)
                    dbg('connecting %s' % self.website)
                    if response:
                        self.website_title = BeautifulSoup(response.read(), 'lxml').title.get_text()
                    else:
                        return
                    if not self.website_title:
                        return

                    response = CorpItem._soqi_conn_pool.request('GET', self.id_page)
                    self.introduction, self.product = CorpItem.get_corp_intro_and_product(BeautifulSoup(response.data, 'lxml'))
                except URLError as e:
                    dbg('!!!!!!!!!!!!%s %s' % (e, self.website.__repr__()))
                except AttributeError as e:
                    dbg('!!!!!!!!!!!!%s has no title' % self.website)
                except ValueError as e:
                    dbg('############%s is url of unknown type' % self.website)


        self.thread = threading.Thread(target=per_thread, args=())
        self.thread.start()
        # thread.join()


    def get_info_as_tuple(self):
        self.thread.join()
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
        print self.id
        print self.corp_name
        print self.introduction
        print self.product
        print self.website
        print self.website_title




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
    soup = BeautifulSoup(data)

    item = CorpItem(soup, 2, '100000')

    item.dump()

