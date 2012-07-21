#-*- coding: utf-8 -*-
#encoding=utf-8

#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')
import MySQLdb

conn=''
cursor=''
#host="localhost"
#user='root'
#passwd='123456'
#db='companyinformation'
#tablename='companyinformation'

def initMysql(host="localhost",user='root',passwd='123456',db='companyinformation'):
    global  conn
    global  cursor
    conn=MySQLdb.connect(host,user,passwd,db,charset="utf8")
    cursor=conn.cursor()


def inserttoMysql(tuple,tablename='companyinformation'):
    sql="insert into "+tablename+" values(%s,%s,%s,%s,%s,%s)"
    try:
        n=cursor.execute(sql,tuple)
    except :
        deletesql="DELETE FROM `companyinformation`.`companyinformation` WHERE `ID`='"+tuple[0]+"'";
        cursor.execute(deletesql,())
        print "去重操作：该数据存在重复,主键无法有相同值，已删除原有数据库中该条数据并重新生成:"
        print "ID:"+tuple[0]
        print "公司名:"+tuple[1]
        n=cursor.execute(sql,tuple)


def finishInsertMysql():
    global conn,cursor
    conn.commit()
    cursor.close()
    conn.close()

if __name__=='__main__':
    infor=("100000_10720K5DHP9Z","安徽省潜山县信兴刷业有限公司","安徽省潜山县信兴刷业有限公司/销售是一家集生产加工、经销批发的股份有限公司，高品质布轮、工业毛刷.是安徽省潜山县信兴刷业有限公司/销售的主营产品。安徽省潜山县信兴刷业有限公司/销售是一家经国家相关部门批准注册的企业。安徽省潜山县信兴刷业有限公司/销售以雄厚的实力、合理的价格、优良的服务与多家企业建立了长期的合作关系。安徽省潜山县信兴刷业有限公司/销售热诚欢迎各界前来参观、考察、洽谈业务。","高品质布轮;工业毛刷.","http://www.qsxxsy.cn","安徽省潜山县信兴刷业有限公司网站")
    initMysql()
    inserttoMysql(infor)
    finishInsertMysql()
