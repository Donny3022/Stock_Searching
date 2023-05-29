# -*- coding: utf-8 -*-
"""
    @Time:2019/4/24 17:59
    @Author: John Ma
"""
from sqlalchemy import create_engine
import xlrd  # 引入模塊
import pandas as pd
import numpy as np
import time

# 時間戳轉化為時間
def timestampToTime(now):  # 時間戳
    now = now
    int(now)
    tl = time.localtime(now)
    # 格式化時間
    format_time = time.strftime("%Y-%m-%d", tl)
    return format_time

def timeToTimestamp(format_time):
    # 格式化時間
    format_time = format_time
    # 時間
    ts = time.strptime(format_time, "%Y-%m-%d")
    # 格式化時間轉時間戳
    return time.mktime(ts)


def createTables_ALLstockCodes_stockCodes(path):
    workbook = pd.read_excel(path)  # 文件路徑
    # 用DBAPI構建數據庫鏈接engine
    engine = create_engine("mysql+pymysql://trading:trading@localhost:3306/job?charset=utf8")

    # 建立連接
    con = engine.connect()
    # print(list(workbook['股票代碼']))
    temp = 123
    list_index = []
    stock_codes = []
    for index, row in workbook.iterrows():
       if temp != row['股票代碼']:
           temp = row['股票代碼']
           stock_codes.append(temp)
           list_index.append(index)

    #將所有股票名稱放入數據庫表stock_codes
    df_stock_code = pd.DataFrame(stock_codes, columns=['stock_code'])
    df_stock_code.to_sql(name="stock_codes", con=con, if_exists='replace',index=False)

    # 由於成交量數據值大，所以將數據縮小方便在圖中顯示
    workbook['成交量'] = workbook['成交量']/1000000
    data_workbook = workbook.rename(columns={'成交量': '成交量(千張)'})
    data_workbook['日期'] = pd.to_datetime(data_workbook['日期']).dt.strftime('%Y-%m-%d')
    print(data_workbook)

    #將每個股票各自分開用各自名字建表
    for index in range(len(list_index)):
        print(index)
        if index < len(list_index)-1:
            df = data_workbook[ list_index[index]+1 : list_index[index+1] ]
            stock_num = str(list(df["股票代碼"])[0])
            df.to_sql(name=stock_num, con=con, if_exists='replace',index=False)
        else:
            df = data_workbook[ list_index[index]+1 : data_workbook.shape[0] ]
            stock_num = str(list(df["股票代碼"])[0])
            df.to_sql(name=stock_num, con=con, if_exists='replace',index=False)


if __name__ == "__main__":
    path = r"E:\Django_Stock_Search-master\DataNow.xlsx"
    createTables_ALLstockCodes_stockCodes(path)