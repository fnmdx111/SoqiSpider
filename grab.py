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
    threads = []

    for args in per_thread_args:
        threads.append(Thread(target=per_thread_func, args=args))
        threads[-1].start()

    for thread in threads:
        thread.join()


def start_multi_threading(keyword, (from_page, to_page), container=None, url='www.soqi.cn', thread_num=20, max_retry=5, func=lambda x: x.corp_name):
    def partition(iterable, by=10):
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
            # 这里执行写入mysql或写入excel的操作
            # 最好异步进行
            # mysql是transactional memory应该没太大问题
            # 异步写入同一个文件可能会有问题，应该仔细考虑
            for page, is_empty_page, items in grab(keyword, pool=conn_pool, pages=pages, func=func):
                dbg('--------------------------%s-----%s-----------------' % (page, is_empty_page))
                if not is_empty_page:
                    grabbed_page_list.append(page)
                    if container:
                        container.extend(items)

        amount = max(set_diff) - min(set_diff)
        by = amount / thread_num + (0 if amount % thread_num == 0 else 1)

        per_thread_args = partition(list(set_diff), by=by)
        dbg('allocated scheme %s' % per_thread_args)

        _start_multi_threading(per_thread, per_thread_args)

        dbg('@@@@@this round l: %s' % grabbed_page_list)
        set_diff -= set(grabbed_page_list)
        retry += 1

        if last_page_found:
            if not set(range(from_page, last_page_found + 1)) & set_diff:
                # 已经抓下来了开始页数，到最后一页的页面
                break

    dbg('escaped from while set_diff')



if __name__ == '__main__':
    def transact(item, file_obj):
        with the_lock:
            print >> file_obj, item.corp_name, ",", item.id

    with open(str(int(time.time() * 100)) + '.txt', 'w') as ff:
        start_multi_threading("公司", (1, 5), max_retry=15, func=functools.partial(transact, file_obj=ff))





