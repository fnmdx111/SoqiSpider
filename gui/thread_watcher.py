# encoding: utf-8
import threading

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time
import sys


class ThreadWatcher(QDialog, object):

    class ContextManager(object):
        def __init__(self, text, host):
            self.text = text
            self.host = host


        def __enter__(self):
            self.host.emit(SIGNAL('registerThread(QString)'), QString(self.text))


        def __exit__(self, exc_type, exc_val, _):
            # print 'emitting signal deleteThread(...) with %s' % self.text
            self.host.emit(SIGNAL('deleteThread(QString)'), self.text)
            if exc_type:
                self.host.emit(SIGNAL('registerThread(QString)'),
                               QString('(!%s: %s)%s' % (exc_type, exc_val, self.text)))


    def __init__(self, parent):
        super(ThreadWatcher, self).__init__(parent)

        self.list_widget = QListWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.connect(self,
                     SIGNAL('registerThread(QString)'),
                     self.register_thread)
        self.connect(self,
                     SIGNAL('deleteThread(QString)'),
                     self.delete_thread)


    def register(self, text):
        return ThreadWatcher.ContextManager(text, self)


    def register_thread(self, text):
        item = QListWidgetItem(text)
        self.list_widget.addItem(item)


    def delete_thread(self, text):
        item = self.list_widget.findItems(text, Qt.MatchExactly)[0]
        self.list_widget.takeItem(self.list_widget.indexFromItem(item).row())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ThreadWatcher(None)
    form.show()

    for item in range(50):
        def func(name):
            with form.register(unicode(name)):
                print 'entering', name
                time.sleep(name)
                print 'exiting', name

        t = threading.Thread(target=func, args=(item,))
        t.start()

    app.exec_()

    # def modify(self, new_text, id):

