# encoding: utf-8

from threading import Thread
import threading
import gui
from reaper import misc
from reaper.misc import partition, to_ellipsis
from reaper.constants import HEADERS
from reaper.spider import grab
from urllib3.connectionpool import HTTPConnectionPool
the_lock = threading.RLock()



def _start_multi_threading(per_thread_func, per_thread_args, flags):
    """启动线程的函数
    per_thread_func: 对于每个线程来说的主函数
    per_thread_args: 应用到主函数上的参数列表"""
    threads = []

    def _(item, args):
        flags[item] = False
        per_thread_func(*args)
        flags[item] = True

    for item, args in enumerate(per_thread_args):
        if gui.misc.STOP_CLICKED:
            return

        threads.append(Thread(target=_, args=(item, args)))
        threads[-1].start()

    for thread in threads:
        # 阻塞以免程序退出
        thread.join(600)


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
        if gui.misc.STOP_CLICKED:
            return

        if retry > max_retry:
            break

        logger.info('关键字: %s 城市号: %s 重试次数: %s\n还剩%s页: %s',
                    keyword, city_code, retry,
                    len(set_diff), to_ellipsis(sorted(set_diff)),)

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
                if gui.misc.STOP_CLICKED:
                    return

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

        flags = [False for _ in range(len(per_thread_args))]
        _start_multi_threading(per_thread, per_thread_args, flags)

        # 对本轮抓取到的页面号进行差分，得到还未抓取的页面号，存储在set_diff中
        set_diff -= set(grabbed_page_list)
        retry += 1

        if misc.last_page_found:
            # 如果找到了最后一页的页码，则将剩余页码中大于等于它的去掉
            set_diff = set(filter(lambda x: x < misc.last_page_found, set_diff))
            logger.info('检测到%s是最后一页', misc.last_page_found)

    logger.debug('escaped from while set_diff')

    return container



