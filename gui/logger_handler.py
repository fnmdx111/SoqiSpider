# encoding: utf-8
from logging import Handler
import threading


class LoggerHandler(Handler):
    def __init__(self, logger_widget):
        self.lock = threading.RLock()
        self.logger_widget = logger_widget
        super(LoggerHandler, self).__init__()


    def emit(self, record):
        self.logger_widget.emit('clicked()')
        # self.logger_widget.append(self.format(record))



