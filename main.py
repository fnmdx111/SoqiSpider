# encoding: utf-8
import threading
from PyQt4.QtGui import *
import sys
from gui.misc import ConfigReader
from gui.main import *
from insert.excel import ExcelWriter
from insert.mysql import MySQLWriter


if __name__ == '__main__':
    excel_writer = ExcelWriter(None, output_name=str(int(time.time())) + '.xls')
    # mysql_writer = MySQLWriter(None)

    def init(logger):
        excel_writer.logger = logger
        # mysql_writer.logger = logger


    def destroy():
        excel_writer.commit()
        # mysql_writer.commit()
        # mysql_writer.finish()


    the_lock = threading.RLock()
    def transact(item):
        if not item.is_valid_item():
            return

        with the_lock:
            excel_writer.insert(item)
            excel_writer.commit()
            excel_writer.next_row()

            # mysql_writer.insert(item)
            # try:
            #     mysql_writer.commit()
            #     pass
            # except BaseException:
            #     pass


    app = QApplication(sys.argv)
    form = Form(transact, config=ConfigReader('Spider.exe.config'), destroyer_func=destroy, initializer_func=init)

    form.show()
    form.thread_watcher.show()

    app.exec_()


