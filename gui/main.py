# encoding: utf-8
import functools
import logging
import threading
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import time
from gui.logger_handler import LoggerHandler
from reaper.content_man import ContentManager
from reaper.grab import start_multi_threading

logging.basicConfig(
    format='%(levelname) 8s %(message)s',
    level=logging.INFO
)


class Form(QDialog, object):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent, )

        self.resize(640, 400)

        self.logger_widget = QTextBrowser()
        self.btn_start = QPushButton('开始'.decode('utf-8'))

        layout = QVBoxLayout()
        layout.setGeometry(QRect(QPoint(0, 0), QSize(640, 400)))
        layout.addWidget(self.btn_start)
        layout.addWidget(self.logger_widget)
        self.setLayout(layout)

        self.logger = logging.getLogger(__name__)
        handler = LoggerHandler(self.logger_widget)
        handler.setFormatter(logging.Formatter(
            fmt='<font color=blue>%(asctime)s</font> <font color=red>%(levelname) 8s</font> %(message)s',
            datefmt='%m/%dT%H:%M:%S'
        ))
        self.logger.addHandler(handler)

        self.connect(self.btn_start, SIGNAL('clicked()'), self.btn_start_click)
        # self.connect(self.logger_widget)


    def btn_start_click(self):
        the_lock = threading.RLock()
        def _():
            def transact(item, file_obj):
                if not item.is_valid_item():
                    return
                with the_lock:
                    print >> file_obj, item.corp_name, ',', item.website_title, ',', item.introduction
                    file_obj.flush()

            with open(str(int(time.time() * 100)) + '.txt', 'w') as ff:
                cont_man = ContentManager(functools.partial(transact, file_obj=ff))
                start_multi_threading('公司', (1, 50), content_man=cont_man, max_retry=15, logger=self.logger)

                # cont_man.join_all()

        # _()
        self.transactor_thread = threading.Thread(target=_)
        self.transactor_thread.start()





if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()


