#encoding:utf-8
from pyExcelerator import *
#create a work book
w = Workbook()
ws = w.add_sheet('user')
 
#create xls header
xls_header = [u'啊userName', 'email', 'tel']
for x in range(0, 3):
    ws.write(0, x, xls_header[x])
 
#write content
ws.write(1, 0, 'admin')
ws.write(1, 1, u'黑admin@admin.com')
ws.write(1, 2, '18888888888')
w.save('test.xls')

