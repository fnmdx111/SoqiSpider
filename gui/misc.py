# encoding: utf-8
from logging import Handler
from PyQt4.QtCore import *
from bs4 import BeautifulSoup


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




class ConfigReader(object):

    attrs = ('start_id', 'end_id', 'from_page', 'to_page', 'thread_amount', 'desc_length', 'sql_conn')
    keys = ('startID', 'endID', 'startPage', 'endPage', 'threadAmount', 'descriptionLength', 'MySQLConnectionString')

    def __init__(self, config_file):
        self.config_file = config_file
        self.read_config()


    def read_config(self):
        soup = BeautifulSoup(self.config_file)
        def _extract(key):
            tag = soup.find(name='add', attrs={'key': key})
            return tag['value'] if tag else ''

        map(lambda (attr, key): self.__setattr__(attr, _extract(key)), zip(ConfigReader.attrs, ConfigReader.keys))


    def to_dict(self):
        return dict(zip(ConfigReader.attrs,
                        map(lambda attr: self.__getattribute__(attr),
                            ConfigReader.attrs)))

template = '''<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <appSettings>
    <!--采集方式：0:继续  1：重新-->
    <add key="spiderType" value="0" />
    <!--开始ID-->
    <add key="startID" value="110101" />
    <!--结束ID-->
    <add key="endID" value="110102" />
    <add key="startPage" value="1" />
    <add key="endPage" value="" />
    <add key="threadAmount" value="" />
    <!--网站描述字符串长度-->
    <add key="descriptionLength" value="250" />
    <!--数据库文件设置
    <add key="MySQLConnectionString" value="\data\company.db3" /> -->
  </appSettings>
</configuration>'''

if __name__ == '__main__':
    reader = ConfigReader(template)

    for item in reader.to_dict().items():
        print item


