# encoding: utf-8
import threading
from PyQt4.QtGui import *
import sys
from gui.misc import ConfigReader
from gui.main import *
from insert.excel import ExcelWriter
from insert.mysql import MySQLWriter
import time

if __name__ == '__main__':

    datetime=time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(time.time()))
    excel_writer = ExcelWriter(None, output_name="companyinformation "+str(datetime) + '.xls')
    try:
        mysql_writer = MySQLWriter(None)
    except BaseException:
        pass
    def init(logger):
        global mysql
        excel_writer.logger = logger
        #mysql_writer=MySQLWriter(logger)
        try:
            mysql_writer.logger = logger
        except BaseException:
            pass

    def destroy():
        excel_writer.commit()
        try:
            mysql_writer.commit()
            mysql_writer.finish()
        except BaseException:
            pass

    the_lock = threading.RLock()
    def transact(item):
        if not item.is_valid_item():
            return

        with the_lock:
            excel_writer.insert(item)
            excel_writer.commit()
            excel_writer.next_row()

            try:
                mysql_writer.insert(item)
                mysql_writer.commit()
            except BaseException:
                pass


    app = QApplication(sys.argv)
    form = Form(transact, config=ConfigReader('Spider.exe.config'), destroyer_func=destroy, initializer_func=init)

    form.show()
    form.thread_watcher.show()

    app.exec_()


