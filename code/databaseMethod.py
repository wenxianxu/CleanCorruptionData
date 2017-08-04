# -*- coding:utf-8 -*-

import pymysql


def data_get(userid,password,database,sql):
    """
    Get data from mysql database.
    """
    connect=pymysql.connect(host="localhost",user=userid,passwd=password,db=database,charset='utf8')
    cursor=connect.cursor()
    try:
        cursor.execute(sql)
        results=cursor.fetchall()
        return results
    except:
        print("can't connect with the database")
        return


