# encoding: utf-8
import logging
import MySQLdb


class MySQLWriter(object):

    SQL_INS = 'insert into %s values(%%s, %%s, %%s, %%s, %%s, %%s)'
    SQL_DEL = "delete from  companyinformation where `ID`='%s'"

    def __init__(self, logger, host='localhost', user='root', password='123456', db='companyinformation'):
        try:
            self.conn = MySQLdb.connect(host, user, password, db, charset='utf8')
            self.cursor = self.conn.cursor()
            self.logger = logger
        except BaseException:
            self.logger.info('mysql数据库服务没有启动')

    def insert(self, obj, table_name='companyinformation'):
        tpl = obj.get_info_as_tuple()
        sql_ins = MySQLWriter.SQL_INS % table_name
        try:
            self.cursor.execute(sql_ins, tpl)
        except BaseException:
            self.cursor.execute(MySQLWriter.SQL_DEL % tpl[0])
            self.logger.info('去重操作: 该数据存在重复,主键无法有相同值，已删除原有数据库中该条数据并重新生成:')
            self.logger.info('ID: %s' % tpl[0])
            self.logger.info('公司名: %s' % tpl[1])

            self.cursor.execute(sql_ins, tpl)


    def commit(self):
        self.conn.commit()


    def finish(self):
        self.cursor.close()
        self.conn.close()



if __name__=='__main__':
    mysql_writer = MySQLWriter(logging.getLogger(__name__))
    info=("100000_10720K5DHP9Z","安徽省潜山县信兴刷业有限公司","安徽省潜山县信兴刷业有限公司/销售是一家集生产加工、经销批发的股份有限公司，高品质布轮、工业毛刷.是安徽省潜山县信兴刷业有限公司/销售的主营产品。安徽省潜山县信兴刷业有限公司/销售是一家经国家相关部门批准注册的企业。安徽省潜山县信兴刷业有限公司/销售以雄厚的实力、合理的价格、优良的服务与多家企业建立了长期的合作关系。安徽省潜山县信兴刷业有限公司/销售热诚欢迎各界前来参观、考察、洽谈业务。","高品质布轮;工业毛刷.","http://www.qsxxsy.cn","安徽省潜山县信兴刷业有限公司网站")

    mysql_writer.insert(info)
    mysql_writer.commit()


