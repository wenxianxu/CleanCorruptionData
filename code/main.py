# -*- coding:utf-8 -*-

import sys
sys.path.append("..")
import textAnalysis
import databaseMethod
from config.config import *



database = 'wenshu_corruption'     #要连接的数据库

#case infomation
sql = ''' SELECT docid,content_html,content_progress  FROM wenshu_corruption.t_anjian
                where content_progress='一审' or content_progress='二审' limit 10
        '''

sql = ''' SELECT docid,content_html,content_progress  FROM wenshu_corruption.t_anjian
                where content_progress='二审' limit 100
        '''

sql = ''' SELECT docid,content_html,content_progress, short_content  FROM wenshu_corruption.t_anjian
                where content_progress='一审' or content_progress='二审'  limit 50
        '''
#sql = ''' select docid,content_html,content_progress, short_content FROM wenshu_corruption.t_anjian
 #           where docid = 'f0e40fa9-8923-45eb-a93d-b2eb0a3674bf'
#        '''


results = databaseMethod.data_get(userid,password,database,sql)

textAnalysis.saveAllCleanedDoc("../output/caseInfo.csv", results)


#document infomation
##doc_item = ['DocID','publish_date','judge_date','court','NO','document_type','final_judgment','title','updatetime']
##doc_sql = '''select docid,publish_date,content_date,court_name,content_num,content_type,
##           content_progress,content_title,updatetime from wenshu_corruption.t_anjian 
##          '''
##
##documents = databaseMethod.data_get(userid,password, database, doc_sql)
##textAnalysis.write_csv("../output/docInfo.csv", doc_item, documents)
##
print("END")
