#encoding:utf-8
from pyExcelerator import *

logger = None

w=Workbook()
ws = w.add_sheet('CompanyInformation')

def initExcel(_logger, worksheet=ws):
    global w,ws, logger

    logger = _logger

    xls_headers=[u"公司ID编码",u"公司名",u"公司简介",u"公司主要产品",u"公司网站",u"公司网站标题"]
    for i in range(0,6):
        worksheet.write(0,i,xls_headers[i])

def insertToExcel(worksheet=ws,row=1,item=0):
    global w,ws
    items=item.get_info_as_tuple()
    for i in range(0,6):
        worksheet.write(row,i,str(items[i]).decode('utf-8'))

def finishExcel(outputname='test.xls'):
    global w
    w.save(outputname)
