# encoding: utf-8
from functools import partial
import logging
import threading
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import time
import gui
from gui.misc import LoggerHandler, ParameterSet, THREAD_AMOUNT_SAFE, ITEM_DENSITY, SUBTHREAD_AMOUNT, ConfigReader
from reaper.misc import take, get_estimate_item_amount
from reaper.constants import REQUIRED_SUFFIXES, AUTO, HEADERS
from reaper.content_man import ContentManager
from reaper.grab import start_multi_threading
from reaper.id_gen import get_ids
from urllib3.connectionpool import HTTPConnectionPool

logging.basicConfig(
    format='',
)


class Form(QDialog, object):

    _CheckBox_keyword_names = map(lambda item: 'cb_' + item, ['company', 'factory', 'corp', 'center', 'inst'])
    _LineEdit_names = map(lambda item: 'le_' + item, ['start_id', 'end_id', 'from_page', 'to_page', 'thread_amount'])

    def __init__(self, transactor_func,
                 initializer_func=None,
                 destroyer_func=None,
                 parameters=None,
                 parent=None,
                 config=None,
                 max_retry=30):
        self.parameters = parameters
        self.transactor_func = transactor_func
        self.destroyer_func = destroyer_func
        self.max_retry=max_retry
        self.logger = logging.getLogger(__name__)
        self.cont_man = ContentManager(self.transactor_func)

        super(Form, self).__init__(parent)

        if initializer_func:
            try:
                initializer_func(self.logger)
            except BaseException as e:
                Form._ask_and_handle(
                    self,
                    (u'出错了',
                     u'发生了如下错误\n%s\n是否退出' % e),
                    (lambda: exit(), lambda: None)
                )

        self.setWindowTitle(u'soqi.cn爬虫')
        self.resize(640, 400)

        self.logger_widget = QTextBrowser()
        self.logger_widget.setFocusPolicy(Qt.NoFocus)

        self.btn_start = QPushButton(u'开始')
        self.btn_start.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))

        layout = QVBoxLayout()
        layout.addLayout(self._gen_LineEdit_layout())
        layout.addLayout(self._gen_CheckBox_layout())
        layout.addWidget(self.logger_widget)
        self.setLayout(layout)

        self.cb_company.setChecked(True)

        self.connect(self.btn_start, SIGNAL('clicked()'), self.btn_start_click)
        self.connect(self.logger_widget, SIGNAL('newLog(QString)'), self.new_log)
        self.connect(self, SIGNAL('jobFinished(QString)'), self.grabbing_finished)
        self.connect(self, SIGNAL('activeThreadCountChanged(int)'), self.active_thread_count_changed)
        self._connect_LineEdit_signals() # 对QLineEdit绑定textChanged信号，对输入是否合法进行检测
        for widget in [self.le_end_id, self.le_to_page]:
            self.connect(widget, SIGNAL('editingFinished()'), self.editing_finished)

        handler = LoggerHandler(self.logger_widget)
        handler.setFormatter(logging.Formatter(
            fmt='<font color=blue>%(asctime)s</font> <font color=red><b>%(levelname) 8s</b></font> %(message)s',
            datefmt='%m/%dT%H:%M:%S'
        ))
        self.logger.addHandler(handler)

        if config: # 必须在QLineEdit控件的信号绑定完毕之后再将config写入，以利用restrict_content检测不合法的输入
            flag = '默认'
            try:
                config.read_config()
                flag = '文件'
            except IOError:
                gui.misc.STOP_CLICKED = False
                self.logger.warning('找不到Spider.exe.config，使用默认配置')
                gui.misc.STOP_CLICKED = True
            finally:
                attrs = ['end_id', 'start_id', 'to_page', 'from_page', 'thread_amount']
                map(lambda (attr, widget): widget.setText(attr),
                    zip(map(lambda attr: config.__getattribute__(attr),
                            attrs),
                        map(lambda attr: self.__getattribute__(attr),
                            map(lambda x: 'le_' + x, attrs))))
                gui.misc.STOP_CLICKED = False
                self.logger.info('成功应用%s配置', flag)
                gui.misc.STOP_CLICKED = True

        def _add_attr(obj_name): # 根据QLineEdit中已有的内容，添加last_content标签，以便在检测到不合法的输入时回滚
            obj = self.__getattribute__(obj_name)
            cont = obj.text()
            obj.last_content = cont
            if cont:
                if not unicode(cont).isdigit():
                    obj.last_content = ''
                    obj.setText(obj.last_content)

        map(_add_attr, Form._LineEdit_names[:-1])

        self.le_end_id.companion = self.le_start_id
        self.le_to_page.companion = self.le_from_page

        self._start_thread_counter()


    def editing_finished(self):
        companion = self.sender().companion
        companion.emit(SIGNAL('textChanged(QString)'), companion.text())


    def _connect_LineEdit_signals(self):
        for item, ref_obj, maximum in zip((self.le_to_page, self.le_from_page, self.le_start_id, self.le_end_id),
                                          (self.le_to_page, self.le_to_page,   self.le_end_id,   self.le_end_id),
                                          ('2000',          AUTO,              AUTO,             '820000')):
            self.connect(item,
                         SIGNAL('textChanged(QString)'),
                         partial(self.restrict_content,
                                 ref_obj=ref_obj))
            item.maximum = maximum


    def _start_thread_counter(self):
        def active_thread_counter():
            current_count = threading.active_count()
            while True:
                if current_count != threading.active_count():
                    current_count = threading.active_count()
                    self.emit(SIGNAL('activeThreadCountChanged(int)'), current_count)

        th = threading.Thread(target=active_thread_counter)
        th.setDaemon(True)
        th.start()


    def active_thread_count_changed(self, count):
        self.setWindowTitle(u'soqi.cn爬虫 活跃线程数: %s' % (count - 1))


    def restrict_content(self, content, ref_obj):
        maximum = self.sender().maximum
        maximum = ref_obj.text() if maximum == AUTO else maximum
        maximum = ref_obj.maximum if not maximum else maximum

        content = unicode(content) # 从QString转换为unicode方便使用python basestring接口操作
        if content:
            if not content.isdigit():
                self.sender().setText(self.sender().last_content)
            elif maximum:
                if int(content) > int(maximum):
                    self.sender().setText(maximum)
            self.last_to_page_content = self.le_to_page.text()


    def _gen_LineEdit_layout(self):
        h_layout = QHBoxLayout()

        def _gen_layout(label, attribute, max_length=6, default='000000'):
            _layout = QHBoxLayout()

            line_edit = QLineEdit()
            line_edit.setText(default)
            line_edit.setFixedSize(max_length * 10, 20)
            line_edit.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
            line_edit.setAlignment(Qt.AlignRight)
            line_edit.setMaxLength(max_length)

            _layout.addWidget(QLabel(label))
            _layout.addWidget(line_edit)

            self.__setattr__(attribute, line_edit)

            return _layout

        h_layout.addStretch()
        h_layout.addWidget(QLabel(u'<font color="red"><b>搜企爬虫</b></font>'))
        h_layout.addStretch()
        h_layout.addWidget(self.btn_start)
        h_layout.addStretch()

        for args in zip((u'起始id:', u'结束id:', u'起始页:', u'结束页:', u'线程数:'),
                        Form._LineEdit_names,
                        (6, 6, 4, 4, 3),
                        ('000000', '999999', '1', '', '')):
            h_layout.addLayout(apply(_gen_layout, args))
            h_layout.addStretch()

        return h_layout


    def _gen_CheckBox_layout(self):
        h_layout = QHBoxLayout()

        h_layout.addWidget(QLabel(u'关键词:'))
        for attr, item in zip(
            Form._CheckBox_keyword_names,
            map(lambda item: item.decode('utf-8'), REQUIRED_SUFFIXES)
        ):
            checkbox = QCheckBox(item)
            checkbox.setChecked(False)
            self.__setattr__(attr, checkbox)
            h_layout.addWidget(checkbox)

        h_layout.addStretch()
        h_layout.addWidget(QLabel(u'若<font color="red">结束页</font>与<font color="red">线程数</font>留空，则自动设置之'))

        return h_layout


    def grabbing_finished(self, job_identity):
        self.logger.info('<b><font color="green">作业 %s 结束</font></b>', unicode(job_identity).encode('utf-8'))
        if not gui.misc.STOP_CLICKED and self.cont_man:
            self.btn_start_click()


    def new_log(self, s):
        self.logger_widget.append(s)


    def get_checked_keywords(self):
        return filter(
            lambda item: item.checkState() == Qt.Checked,
            map(
                lambda item: self.__getattribute__(item),
                Form._CheckBox_keyword_names
            )
        )


    def start_threads(self, parameters):
        # 单位时间总线程数: THREAD_AMOUNT_SAFE * thread_num + 企业数 / C < 500
        self.logger.debug('starting threads')

        conn_pool = HTTPConnectionPool(host='www.soqi.cn', headers=HEADERS)

        def _(params):
            cont_man = ContentManager(self.transactor_func)
            for param in params:
                for keyword in map(lambda item: unicode(item.text()).encode('utf-8'), self.get_checked_keywords()):
                    if gui.misc.STOP_CLICKED:
                        return

                    if param.to_page == AUTO:
                        self.logger.info('自动检测结束页... 正在获取粗略项目数量')
                        item_amount = get_estimate_item_amount(keyword, param.city_id, conn_pool, self.logger)
                        if item_amount > 0:
                            param.to_page = int(item_amount / ITEM_DENSITY) + 1
                        else:
                            param.to_page = 2000
                        self.logger.info('总项目数量: %s, 估计结束页: %s', item_amount, param.to_page)

                    self.logger.info(
                        '开始: 关键字 %s, 城市号 %s, (%d, %d)',
                        keyword, param.city_id.encode('utf-8'),
                        param.from_page, param.to_page
                    )

                    start_multi_threading( # 这个函数开启thread_num个线程
                        keyword,
                        (param.from_page, param.to_page),
                        city_code=param.city_id,
                        content_man=cont_man,
                        max_retry=self.max_retry,
                        thread_num=THREAD_AMOUNT_SAFE,
                        logger=self.logger
                    )

            while not cont_man.job_done():
                pass
            self.emit(SIGNAL('jobFinished(QString)'), QString('%s to %s' % (params[0].city_id, params[-1].city_id)))

        def dummy():
            for sub_params in take(parameters, by=int(self.thread_amount / SUBTHREAD_AMOUNT)): # e.g. by=300 / 20 = 15 即一次并发抓取15个city_id
                if gui.misc.STOP_CLICKED:
                    return

                _(sub_params)
                # self.logger.info('当前并发抓取的id为: %s', map(lambda item: item.city_id + ' ' + item.keyword, sub_params))
                # transactor_thread = threading.Thread(target=_, args=(sub_params,)) # 这个线程开启THREAD_AMOUNT_SAFE个线程
                # transactor_thread.setDaemon(True)
                # transactor_thread.start()
                # transactor_thread.join() # 阻塞，防止一次启动多个抓取主线程，吃不消

        t = threading.Thread(target=dummy)
        t.setDaemon(True)
        t.start() # 新启动一个线程，以免阻塞ui线程


    def prepare_parameters(self):
        def _prepare_parameters(start_id, end_id, from_page, to_page):
            params = []
            for city_id in get_ids(start_id, end_id):
                    params.append(ParameterSet((from_page, to_page), city_id.encode('utf-8')))

            return params

        (start_id, end_id,
        from_page, to_page,
        self.thread_amount) = map(
            lambda widget_name: unicode(self.__getattribute__(widget_name).text()),
            Form._LineEdit_names
        )
        if not (start_id and end_id and from_page):
            self.logger.error('请输入有效的值')
            return

        if not to_page:
            to_page = AUTO
        if not self.thread_amount:
            self.thread_amount = AUTO
            self.thread_amount = min(self.thread_amount, THREAD_AMOUNT_SAFE)

        self.logger.debug(
            'start_id: %s, end_id: %s, from_page: %s, to_page: %s, thread_amount: %s',
            start_id, end_id,
            from_page, to_page,
            self.thread_amount
        )

        return _prepare_parameters(start_id, end_id, int(from_page), int(to_page))


    def has_valid_inputs(self):
        _get_texts = lambda iterable: map(lambda _: unicode(self.__getattribute__(_).text()), iterable)

        start_id, end_id = _get_texts(('le_start_id', 'le_end_id'))
        if any(map(lambda _: not (_.isdigit() and len(_) == 6), (start_id, end_id))):
            self.logger.error('起始id和结束id必须为六位整数')
            return False
        if start_id > end_id:
            self.logger.error('起始id必须小于等于结束id')
            return False

        from_page, to_page = _get_texts(('le_from_page', 'le_to_page'))
        if from_page.isdigit():
            if to_page.isdigit():
                if int(to_page) > 2000:
                    self.logger.error('结束页必须小于等于2000')
                    return False
                if from_page > to_page:
                    self.logger.error('起始页必须小于等于结束页')
                    return False
            elif to_page and not to_page.isdigit():
                self.logger.error('结束页必须为小于三位的整数')
                return False
        else:
            self.logger.error('起始页必须为小于三位的整数')
            return False

        return True


    def btn_start_click(self):
        gui.misc.STOP_CLICKED = not gui.misc.STOP_CLICKED

        if not gui.misc.STOP_CLICKED:
            self.logger.debug(
                '%s checked',
                ' '.join(map(lambda item: unicode(item.text()).encode('utf-8'), self.get_checked_keywords())))

            if not self.has_valid_inputs():
                return

            self.btn_start.setText(u'停止')
            self.start_threads(self.prepare_parameters())
        else:
            self.logger.warning('stop clicked')
            self.btn_start.setText(u'开始')


    @staticmethod
    def _ask_and_handle(widget, (msg_title, msg_body), (yes_callback, no_callback)):
        reply = QMessageBox.question(
            widget,
            msg_title,       msg_body,
            QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            yes_callback()
        else:
            no_callback()


    def closeEvent(self, event):
        callbacks = (lambda: event.accept(), lambda: event.ignore())
        try:
            if self.destroyer_func:
                self.destroyer_func()
                event.accept()
            if threading.active_count() > 20:
                Form._ask_and_handle(
                    self,
                    (u'仍然退出？',
                    u'检测到活动线程数大于20，如果仍然退出可能会崩溃'),
                    callbacks
                )
        except BaseException as e:
            Form._ask_and_handle(
                self,
                (u'出错了',
                u'发生了如下错误\n%s\n是否退出' % e),
                callbacks
            )



if __name__ == '__main__':
    with open(str(int(time.time() * 100)) + '.txt', 'w') as ff:
        the_lock = threading.RLock()
        def transact(item):
            if not item.is_valid_item():
                return
            with the_lock:
                print >> ff, item.corp_name, ',', item.website_title, ',', item.introduction
                ff.flush()


        app = QApplication(sys.argv)
        form = Form(transact,
                    config=ConfigReader('Spider.exe.config'),)
        form.show()
        app.exec_()


