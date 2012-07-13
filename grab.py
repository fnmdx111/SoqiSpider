# encoding: utf-8

import functools
from threading import Thread
import threading
import time
from constants import headers
from spider import grab, last_page_found
from urllib3.connectionpool import HTTPConnectionPool
from common import dbg


the_lock = threading.RLock()

def _start_multi_threading(per_thread_func, per_thread_args):
    """启动线程的函数
    per_thread_func: 对于每个线程来说的主函数
    per_thread_args: 应用到主函数上的参数列表"""
    threads = []

    for args in per_thread_args:
        threads.append(Thread(target=per_thread_func, args=args))
        threads[-1].start()

    for thread in threads:
        # 阻塞以免程序退出
        thread.join()


def start_multi_threading(
        keyword,
        (from_page, to_page),
        city_code='100000',
        container=None,
        func=lambda x: x.corp_name,
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
    def partition(iterable, by=10):
        """按每by个把iterable分成若干组"""
        if not by:
            return [iterable]
        return [iterable[i * by:(i + 1) * by] for i in range(len(iterable) / by  + (1 if len(iterable) % by != 0 else 0))]

    conn_pool = HTTPConnectionPool(host=url, maxsize=thread_num, block=True, headers=headers)

    retry = 1

    range_all = range(from_page, to_page + 1)
    set_all = set(range_all)
    set_diff = set_all

    while set_diff:
        if retry > max_retry:
            break

        dbg('remaining %s pages: %s, retry: %s' % (len(set_diff), sorted(set_diff), retry))

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
                func=func,
                city_code=city_code,
                predicate=predicate
            )
            for page, is_empty_page, grabbed_items in grabber:
                if not is_empty_page:
                    grabbed_page_list.append(page)
                    if container:
                        container.extend(grabbed_items)

        # 平均分配任务，其中by的算法是对总数÷线程数之后向上取整，可以保证分配出的子方案数小于线程数
        amount = max(set_diff) - min(set_diff)
        by = amount / thread_num + (0 if amount % thread_num == 0 else 1)

        # 对还剩下没抓的页面号进行分配
        per_thread_args = partition(list(set_diff), by=by)
        dbg('allocated scheme %s' % per_thread_args)

        _start_multi_threading(per_thread, per_thread_args)

        # 对本轮抓取到的页面号进行差分，得到还未抓取的页面号，存储在set_diff中
        set_diff -= set(grabbed_page_list)
        retry += 1

        if last_page_found:
            # 如果找到了最后一页，且已抓到的页面号与未抓到的页面号的交集为空，表示已抓取完毕
            #               已经抓下来了开始页数，到最后一页的页面
            if not set(range(from_page, last_page_found + 1)) & set_diff:
                break

    dbg('escaped from while set_diff')

    return container


if __name__ == '__main__':
    def transact(item, file_obj):
        with the_lock:
            item.dump()
            print >> file_obj, item.corp_name, ",", item.id, ",", item.introduction, ",", item.website, ",", item.website_title

    with open(str(int(time.time() * 100)) + '.txt', 'w') as ff:
        start_multi_threading("公司", (1, 5), max_retry=15, func=functools.partial(transact, file_obj=ff))





