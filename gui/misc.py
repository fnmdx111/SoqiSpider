# encoding: utf-8
from logging import Handler
from PyQt4.QtCore import *


THREAD_AMOUNT_SAFE = 200
SUBTHREAD_AMOUNT = 20

STOP_CLICKED = True

ITEM_DENSITY = 7 # this means every page has 7 items in average

class LoggerHandler(Handler):
    def __init__(self, logger_widget):
        self.logger_widget = logger_widget
        self.locked = False
        super(LoggerHandler, self).__init__()


    def emit(self, record):
        if STOP_CLICKED:
            if not self.locked:
                self.logger_widget.emit(SIGNAL('newLog(QString'), u'请耐心等待线程停止...')
                self.locked = True
        else:
            self.locked = False
            self.logger_widget.emit(SIGNAL('newLog(QString)'), self.format(record).decode('utf-8'))
        # self.logger_widget.append(self.format(record))




class ParameterSet(object):
    def __init__(self, (from_page, to_page), city_id):
        self.from_page, self.to_page = from_page, to_page
        self.city_id = city_id


    def __str__(self):
        return ' '.join(map(str, [self.from_page, self.to_page, self.city_id]))




