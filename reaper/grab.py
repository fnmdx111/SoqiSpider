# encoding: utf-8

import functools
from threading import Thread
import threading
import time
from reaper import misc
import reaper
from reaper.misc import partition
from reaper.constants import HEADERS
from reaper.content_man import ContentManager
from reaper.spider import grab
from urllib3.connectionpool import HTTPConnectionPool
import mysql
import excel
the_lock = threading.RLock()



def _start_multi_threading(per_thread_func, per_thread_args):
    """启动线程的函数
    per_thread_func: 对于每个线程来说的主函数
    per_thread_args: 应用到主函数上的参数列表"""
    threads = []

    for args in per_thread_args:
        threads.append(Thread(target=per_thread_func, args=args))
        threads[-1].start()

    # for thread in threads:
    #     # 阻塞以免程序退出
    #     thread.join()


def start_multi_threading(
        keyword,
        (from_page, to_page),
        content_man,
        logger=None,
        city_code='100000',
        container=None,
        max_retry=5,
        predicate=None,
        thread_num=20,
        url='www.soqi.cn'
    ):
    """根据所给参数开始多线程抓取
    from_page: 起始页面，注意最低不过1
    to_page: 结束页面，无上限，自动判断
    container: 如果container不是None，则视为需要把CorpItem对象储存起来，以供后用
    func: 接受一个CorpItem对象，返回值会被丢弃，表示要对每一个CorpItem对象进行的操作，比如输出到文件
    max_retry: 最大尝试次数
    thread_num: 最大线程数（并不包含CorpItem对象检索主页标题的线程）
    url: 创建连接池所用的host
    返回: 装载了所抓取的CorpItem对象的container
    其他同_grab，略"""

    conn_pool = HTTPConnectionPool(host=url, maxsize=thread_num, block=True, headers=HEADERS)

    retry = 1

    to_page = min(to_page, 2000)

    range_all = range(from_page, to_page + 1)
    set_all = set(range_all)
    set_diff = set_all

    while set_diff:
        if retry > max_retry:
            break

        logger.info('remaining %s pages: %s, retry: %s', len(set_diff), sorted(set_diff), retry)

        grabbed_page_list = []
        def per_thread(*pages):
            """略
            注: 因为Thread将给定的参数列表打散后传给per_thread，所以需要将参数再收集回列表"""
            # 这里执行写入mysql或写入excel的操作
            # 最好异步进行
            # mysql是transactional memory应该没太大问题
            # 异步写入同一个文件可能会有问题，应该仔细考虑
            grabber = grab(
                keyword,
                pool=conn_pool,
                pages=pages,
                city_code=city_code,
                logger=logger,
                predicate=predicate
            ) # 注意grabber是一个生成器
            for page, is_empty_page, grabbed_items in grabber:
                if not is_empty_page:
                    grabbed_page_list.append(page)
                    if container:
                        container.extend(grabbed_items)
                    content_man.register_objects(grabbed_items)


        # 平均分配任务，其中by的算法是对总数÷线程数之后向上取整，可以保证分配出的子方案数小于线程数
        amount = max(set_diff) - min(set_diff)
        by = amount / thread_num + (0 if amount % thread_num == 0 else 1)

        # 对还剩下没抓的页面号进行分配
        per_thread_args = partition(list(set_diff), by=by)
        logger.debug('allocated scheme %s', per_thread_args)

        _start_multi_threading(per_thread, per_thread_args)

        # 对本轮抓取到的页面号进行差分，得到还未抓取的页面号，存储在set_diff中
        set_diff -= set(grabbed_page_list)
        retry += 1

        if misc.last_page_found:
            # 如果找到了最后一页的页码，则将剩余页码中大于等于它的去掉
            set_diff = set(filter(lambda x: x < misc.last_page_found, set_diff))

    logger.debug('escaped from while set_diff')

    return container

if __name__ == '__main__':
    row=0
    def transact(item, file_obj):
        global row
        if not item.is_valid_item():
            return
        with the_lock:
            #print >> file_obj, item.corp_name, ',', item.id, ',', item.introduction, ',', item.website, ',', item.website_title

            #row控制写入行数,写入excel
            row+=1
            excel.insertToExcel(row=row,item=item)

            #写入mysql
            mysql.inserttoMysql(item.get_info_as_tuple())

            #写入txt
            file_obj.write(item.corp_name+"\n       ID:"+item.id+"\n       公司简介:"+item.introduction+"\n       主要产品关键词:"+item.product+"\n       网址:"+item.website+"\n       网址标题:"+item.website_title+'\n')
            file_obj.flush()

    #初始化要写入的表格
    excel.initExcel()

    #初始化要写入的mysql数据库
    #默认 host地址="localhost"，用户名='root'，密码='123456'，数据库名='companyinformation'，插入表名='companyinformation'
    mysql.initMysql()


    with open(str(int(time.time() * 100)) + '.txt', 'w') as ff:
        cont_man = ContentManager(functools.partial(transact, file_obj=ff))
        start_multi_threading('公司', (1, 2),thread_num=1,content_man=cont_man, max_retry=15, logger=reaper.logger)
        cont_man.join_all()

        #写入完毕，保存excel ,输出文件名可以自定义
        outputname="OutputCompanyInfor.xls"
        excel.finishExcel(outputname)

        #写入完毕，提交mysql
        mysql.finishInsertMysql()

