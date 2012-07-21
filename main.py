# encoding: utf-8
import threading
from PyQt4.QtGui import *
import sys
import time
from gui.misc import ConfigReader
from gui.main import *
import insert.excel
import insert.mysql

def finishinsert():
    #写入完毕，保存excel ,输出文件名可以自定义
    insert.excel.finishExcel("companyinformation.xls")
    #写入完毕，提交mysql
    insert.mysql.finishInsertMysql()

def initializer_func():
#初始化要写入的表格
    insert.excel.initExcel()
    #初始化要写入的mysql数据库
    #默认 host地址="localhost"，用户名='root'，密码='123456'，数据库名='companyinformation'，插入表名='companyinformation'
    try:
        insert.mysql.initMysql()
    except :
        pass
        #TODO 提示mysql没有成功建立连接
        #PyQt4.QtGui.QMessageBox.Question(self,)

def init():
    insert.excel.initExcel()
    insert.mysql.initMysql()


if __name__ == '__main__':
    row=0
    date=time.strftime("%Y-%m-%d %H %M %S",time.localtime(time.time()))
    date=str(date)

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
            #TODO 这里调用初始化函数，需要放到窗口里
        #initializer_func()

        app = QApplication(sys.argv)
        form = Form(transact, config=ConfigReader('Spider.exe.config'), destroyer_func=finishinsert, initializer_func=init)
        form.show()
        app.exec_()
        # form = Form(destroyer_func=finishinsert)


