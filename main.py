# encoding: utf-8
import logging
import threading
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import time
import gui
from gui.misc import LoggerHandler, ParameterSet, THREAD_AMOUNT_SAFE, ITEM_DENSITY, SUBTHREAD_AMOUNT, ConfigReader
from reaper.misc import take, get_estimate_item_amount
from reaper.constants import REQUIRED_SUFFIXES, AUTO
from reaper.content_man import ContentManager
from reaper.grab import start_multi_threading
from reaper.id_gen import get_ids
from urllib3.connectionpool import HTTPConnectionPool
from gui.main import *
import insert.excel
import insert.mysql

if __name__ == '__main__':
    row=0
    date=time.strftime("%Y-%m-%d %H %M %S",time.localtime(time.time()))
    date=str(date)
    #初始化要写入的表格
    insert.excel.initExcel()

    #初始化要写入的mysql数据库
    #默认 host地址="localhost"，用户名='root'，密码='123456'，数据库名='companyinformation'，插入表名='companyinformation'
    insert.mysql.initMysql()

    with open(date + '.txt', 'w') as ff:
        the_lock = threading.RLock()
        def transact(item):
            if not item.is_valid_item():
                return
            with the_lock:
                #print >> ff, item.corp_name, ',', item.website_title, ',', item.introduction
                #ff.flush()
                global row
                #row控制写入行数,写入excel
                row+=1
                insert.excel.insertToExcel(row=row,item=item)
                #insert.excel.finishExcel("companyinformation.xls")
                #写入mysql
                insert.mysql.inserttoMysql(item.get_info_as_tuple())
                insert.mysql.conn.commit()
                #写入txt
                ff.write(item.corp_name+"\n       ID:"+item.id+"\n       公司简介:"+item.introduction+"\n       主要产品关键词:"+item.product+"\n       网址:"+item.website+"\n       网址标题:"+item.website_title+'\n')
                ff.flush()


        app = QApplication(sys.argv)
        form = Form(transact, config=ConfigReader(gui.misc.template))
        form.show()
        app.exec_()
        #TODO 这两句需要放在析构的时候
        #写入完毕，保存excel ,输出文件名可以自定义
        insert.excel.finishExcel("companyinformation.xls")

        #写入完毕，提交mysql
        insert.mysql.finishInsertMysql()


