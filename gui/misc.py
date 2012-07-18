# encoding: utf-8
from logging import Handler
from PyQt4.QtCore import *
import threading


THREAD_AMOUNT_SAFE = 300
SUBTHREAD_AMOUNT = 20

ITEM_DENSITY = 7 # this means every page has 7 items in average

class LoggerHandler(Handler):
    def __init__(self, logger_widget):
        self.lock = threading.RLock()
        self.logger_widget = logger_widget
        super(LoggerHandler, self).__init__()


    def emit(self, record):
        self.logger_widget.emit(SIGNAL('newLog(QString)'), self.format(record).decode('utf-8'))
        # self.logger_widget.append(self.format(record))




class ParameterSet(object):
    def __init__(self, keyword, (from_page, to_page), city_id):
        self.keyword = keyword
        self.from_page, self.to_page = from_page, to_page
        self.city_id = city_id


    def __str__(self):
        return ' '.join(map(str, [self.keyword, self.from_page, self.to_page, self.city_id]))




