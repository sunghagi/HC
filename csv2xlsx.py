#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: euckr -*-
import argparse
import csv
import os, glob
import sys
import xlsxwriter
import datetime
from lib.vms_hc import *


def csv_to_full_xlsx(date):
   list_of_files = glob.glob(date+"*.csv")                       
   if len(list_of_files) == 0:
      print("%s HC result csv file does not exist.!!" % date)
      sys.exit()
   list_of_files.sort()
   logger.info('%s :: HC result csv files %s', GetCurFunc(), list_of_files)

   config = ConfigLoad()
   try:
      xlsx_filename = config.get_item_from_section('main', 'xlsx_filename')
   except Exception as e:
      logger.exception('%s :: %s', GetCurFunc(), e)
      print('hc.cfg / [main] / xlsx_filename does not exist!!')
      logger.info('hc.cfg / [main] / xlsx_filename does not exist!!')
      sys.exit()

   logger.info('%s :: xlsx_filename : %s', GetCurFunc(), xlsx_filename)

   workbook = xlsxwriter.Workbook(date+ '_' + xlsx_filename + '_' + '2' +'.xlsx')
#   workbook = xlsxwriter.Workbook(date+ '_' + xlsx_filename + '.xlsx')
   worksheet = workbook.add_worksheet(xlsx_filename)    

   format_title = workbook.add_format({
   'text_wrap': True,
   'bold': True,
   'font_size': 12,
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'left',
   'valign' : 'vcenter',
   })
   format = workbook.add_format({
   'text_wrap': True,
   'font_size': 10,
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'center',
   'valign' : 'vcenter',
   'border' : 1
   })
   format_head = workbook.add_format({
   'text_wrap': True,
   'bold': True,
   'font_size': 10,
   'font_color': 'white',
   'bg_color': 'blue',
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'center',
   'valign' : 'vcenter',
   'border' : 1
   })
   format_output = workbook.add_format({
   'text_wrap': True,
   'font_size': 10,
   'font_name': '돋움체'.decode("euc-kr"),
   'valign' : 'vcenter',
   'shrink' : True,
   'border' : 1
   })

   worksheet.merge_range('A1:H1','[ ' + xlsx_filename + u' ]- 월간 점검 결과 ( '+date+' )', format_title)
   worksheet.write('A3', 'No', format_head)
   worksheet.write('B3', '점검일'.decode("euc-kr"), format_head)
   worksheet.write('C3', '점검주기'.decode("euc-kr"), format_head)
   worksheet.write('D3', '차수'.decode("euc-kr"),format_head)
   worksheet.write('E3', '서버'.decode("euc-kr"), format_head)
   worksheet.write('F3', '점검내용'.decode("euc-kr"), format_head)
   worksheet.write('G3', '점검결과'.decode("euc-kr"), format_head)
   worksheet.write('H3', '상세결과'.decode("euc-kr"), format_head)

   row = 3
   for index, file_in_list in enumerate(list_of_files):     
#      print file_in_list
      with open(file_in_list, 'rb') as f:   
          content = csv.reader(f)
          col = 0
          for index, checkday, check_mode, system_name, hostname, item_desc, result, output in content :
             worksheet.write(row, col,     index, format)
             worksheet.write(row, col + 1, checkday, format)
             worksheet.write(row, col + 2, check_mode, format)
             worksheet.write(row, col + 3, system_name, format)
             worksheet.write(row, col + 4, hostname, format)
             worksheet.write(row, col + 5, item_desc.decode("euc-kr"), format)
             worksheet.write(row, col + 6, result, format)
             worksheet.write(row, col + 7, output.decode("euc-kr",'ignore'), format_output)
             row += 1

#   for idx_row, data_in_row in enumerate(result_list):
#      idx_row += 3
#      for idx_col, data_in_cell in enumerate(data_in_row):
#         if type(data_in_cell) == str:
#            data_in_cell = data_in_cell.decode("euc-kr")
#         worksheet.write(idx_row, idx_col, data_in_cell, format)

   worksheet.set_row(0,27)
   worksheet.set_row(2,27)

   worksheet.set_column(0,0,4)
   worksheet.set_column(1,1,10)
   worksheet.set_column(2,2,12)
   worksheet.set_column(3,3,7)
   worksheet.set_column(4,4,12)
   worksheet.set_column(5,5,22)
   worksheet.set_column(6,6,8)
   worksheet.set_column(7,7,120)

   worksheet.set_zoom(85)
   worksheet.autofilter('A3:H'+str(row))

   workbook.close()

def get_between_char(str):
   return (str.split('_'))[1].split('.')[0]

def csv_to_summ_xlsx(date):
   list_of_files = glob.glob(date+"*.csv")                       
   if len(list_of_files) == 0:
      print("%s HC result csv file does not exist.!!" % date)
      sys.exit()
   list_of_files.sort()
   logger.info('%s :: HC result csv files %s', GetCurFunc(), list_of_files)

   config = ConfigLoad()
   try:
      xlsx_filename = config.get_item_from_section('main', 'xlsx_filename')
   except Exception as e:
      logger.exception('%s :: %s', GetCurFunc(), e)
      print('hc.cfg / [main] / xlsx_filename does not exist!!')
      logger.info('hc.cfg / [main] / xlsx_filename does not exist!!')
      sys.exit()

   logger.info('%s :: xlsx_filename : %s', GetCurFunc(), xlsx_filename)

   filename = date+ '_' + xlsx_filename + '_' + '1' +'.xlsx'
   workbook = xlsxwriter.Workbook(filename, {'strings_to_numbers': True})

   sheetname = u"점검걸과"
   worksheet = workbook.add_worksheet(sheetname)    

   format_title = workbook.add_format({
   'text_wrap': True,
   'bold': True,
   'font_size': 10,
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'left',
   'valign' : 'vcenter',
   })
   format = workbook.add_format({
   'text_wrap': True,
   'font_size': 10,
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'center',
   'valign' : 'vcenter',
   'border' : 1
   })
   format_head = workbook.add_format({
   'text_wrap': True,
   'bold': True,
   'font_size': 10,
   'font_color': 'white',
   'bg_color': 'blue',
   'font_name': '돋움체'.decode("euc-kr"),
   'align' : 'center',
   'valign' : 'vcenter',
   'border' : 1
   })
   format_output = workbook.add_format({
   'text_wrap': True,
   'font_size': 10,
   'font_name': '돋움체'.decode("euc-kr"),
   'valign' : 'vcenter',
   'shrink' : True,
   'border' : 1
   })


   col = 0
   count_col = 5

   for index, file_in_list in enumerate(list_of_files):     
      result_start_row = 3
      title_merge_row = 1

#      print file_in_list
      merge_text = get_between_char(file_in_list)

      worksheet.write(2, col, 'No', format_head)
      worksheet.write(2, col + 1, '차수'.decode("euc-kr"),format_head)
      worksheet.write(2, col + 2, '서버'.decode("euc-kr"), format_head)
      worksheet.write(2, col + 3, '점검내용'.decode("euc-kr"), format_head)
      worksheet.write(2, col + 4, '결과'.decode("euc-kr"), format_head)

      with open(file_in_list, 'rb') as f:   
         content = csv.reader(f)
         for index, checkday, check_mode, system_name, hostname, item_desc, result, output in content :
            worksheet.write(result_start_row, col,     index, format)
            worksheet.write(result_start_row, col + 1, system_name, format)
            worksheet.write(result_start_row, col + 2, hostname, format)
            worksheet.write(result_start_row, col + 3, item_desc.decode("euc-kr"), format)
            worksheet.write(result_start_row, col + 4, result, format)
            result_start_row += 1
         # 열너비 지정
         worksheet.set_column(col+0, col+0,  4)
         worksheet.set_column(col+1, col+1,  7)
         worksheet.set_column(col+2, col+2, 11)
         worksheet.set_column(col+3, col+3, 22)
         worksheet.set_column(col+4, col+4,  5)

      worksheet.conditional_format(3, col+4, result_start_row, col+4, {'type':     'text',
                                                                       'criteria': 'containing',
                                                                       'value':    'NOK',
                                                                       'format':   format_head}) 
      worksheet.autofilter(2, 0, result_start_row, col+4)
      worksheet.merge_range(title_merge_row, col, title_merge_row, col+4,'< ' + merge_text + u' > - '+ str(result_start_row-3) + u'항목 OK', format_title)
      col = col + count_col + 1

   worksheet.set_row(0,17)
   worksheet.set_row(1,17)
   worksheet.set_row(2,17)

   worksheet.set_zoom(85)


   workbook.close()

def is_date(date): 
   try:
      datetime.datetime.strptime(date, '%Y%m%d')
   except Exception as e:
      logger.exception('%s :: %s', GetCurFunc(), e)
      msg = "%s : Incorrect data format, should be YYYYMMDD" % date
      raise argparse.ArgumentTypeError(msg) 

   return date 

def main():
   parser = argparse.ArgumentParser(description="IOK Company Health Check Tool.")

   parser.add_argument('-d', '--date', action='store', required=True, 
	type=is_date,
	help="DATE, ex) 2017-09-03, 20170903")

   args = parser.parse_args()

   csv_to_summ_xlsx(args.date) 
   csv_to_full_xlsx(args.date) 

if __name__ == '__main__':
   main()
