#-*-coding:utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render


# Create your views here.
import json
from django.http import HttpResponse
from django.template import loader
import pandas as pd
from pyecharts import Kline, Line, Overlap, Bar, Grid
from django.http import JsonResponse
from sqlalchemy import create_engine

from django.views.decorators.csrf import csrf_exempt
from pandas.core.frame import DataFrame
# 定義存放靜態文件的路徑
REMOTE_HOST = "../static/js/pyecharts/js"

@csrf_exempt
def Hm(request):
    stock_code = request.POST.get("stock_code")
    #print(stock_code)
    if stock_code == None:
        stock_code = str(2330)
    print(stock_code)
    template = loader.get_template('Hyperbolic_map/Hyperbolic_map.html')
    sl = line_smooth(stock_code)
    context = dict(
        myechart=sl.render_embed(),
        host=REMOTE_HOST,
        script_list=sl.get_js_dependencies()
    )
    return HttpResponse(template.render(context, request))

@csrf_exempt
def Hm2(request):
    stock_code = request.POST.get("stock_code")
    print(stock_code)
    if stock_code == "None":
        stock_code = 2330

    template = loader.get_template('Hyperbolic_map/Hyperbolic_map.html')
    sl = line_smooth(stock_code)

    return HttpResponse(sl.render_embed())

def tooltip_formatter(params):
    #
    # temp_params = params.tolist()
    # for i in range(len(temp_params)):
    #     temp_params[i] = "備註：" + str(temp_params[i])
    # params = np.array(temp_params)
    # print(params)
    return params

#圖表主要函式
def line_smooth(stock_code):
    engine = create_engine("mysql+mysqldb://trading:trading@localhost:3306/Job?charset=utf8")
    con = engine.connect()
    sqlcmd = "select * from `" + stock_code + "`"
    stock_All = pd.read_sql_query(sqlcmd, con=engine)
    # 獲取柱圖中需要的數據
    stock = stock_All[[u'日期', u'股票代碼', u'股票名稱', u'成交量(千張)', u'收盤價', u'漲跌幅百分比', u'漲跌幅']]
    stock_new = stock
    stock_new_sorted = stock_new.sort_values('日期', ascending=True)
    stock_code = str(stock_new_sorted['股票代碼'][0])
    stock_name = stock_new_sorted['股票名稱'][0]
    index = stock_new_sorted['日期']
    quote_change = stock_new_sorted['漲跌幅']
    close = stock_new_sorted['收盤價']
    Margin_Balance = stock_new_sorted['成交量(千張)']
    line = Line( stock_code + stock_name +" "+ "成交量、股價雙曲線圖" )
    line.add("股價", index, close, is_smooth=True,
             is_datazoom_show=True, datazoom_type="both",  # 展示最下面那條拖動欄並且共用
             is_xaxis_show=True,  #展示x軸的內容
             line_type = 'solid',
             is_xaxislabel_align=True,  # 展示x軸的標籤
             tooltip_axispointer_type = 'cross',
             tooltip_trigger='axis',
            #tooltip_formatter=tooltip_formatter(quote_change),
             is_more_utils=bool, datazoom_range=[80, 100])

    bar = Bar()
    bar.add("成交量(千張)",
            label_color='black',
            legend_top='1',
            x_axis=stock_new_sorted['日期'],
            y_axis=Margin_Balance,
            is_datazoom_show=True,
            is_stack=True,
            is_xaxislabel_align=True,
            xaxis_line_color="green",
            is_label_show=False,
            datazoom_range=[80, 100],
            )

    overlap = Overlap(width=1300, height=300)

    overlap.add(line)
    overlap.add(bar)

    return overlap

import time
# 時間戳轉化為時間
def timestampToTime(now):  # 時間戳
    now = now
    int(now)
    tl = time.localtime(now)
    # 格式化時間
    format_time = time.strftime("%Y-%m-%d", tl)
    return format_time

# 時間轉為時間戳
def timeToTimestamp(format_time):
    # 格式化時間
    format_time = format_time
    # 時間
    ts = time.strptime(format_time, "%Y-%m-%d")
    # 格式化時間轉時間戳
    return time.mktime(ts)

# 計算並且返回前端需要的函數——json格式
def get_period(df_stock_code, startTime, endTime, IDFinance=None, quote_change=None):
    # 用DBAPI構建數據庫鏈接engine
    engine = create_engine("mysql+pymysql://trading:trading@localhost:3306/Job?charset=utf8")
    # 建立連接
    con = engine.connect()

    #獲取開始和結束時間的index
    endIndex = 0
    startIndex = 0
    for index, row in df_stock_code.iterrows():
        if timeToTimestamp(endTime) >= timeToTimestamp(row['日期']):
            endIndex = row['index']
            break
    for index, row in df_stock_code.iterrows():
        if timeToTimestamp(startTime) == timeToTimestamp(row['日期']):
            startIndex = row['index']
            break
        elif timeToTimestamp(startTime) > timeToTimestamp(row['日期']):
            startIndex = row['index'] -1
            break
    if startIndex == 0:
        startIndex = len(df_stock_code['index'].tolist())



    #當temp_IDFinance=0時，為不符合條件;當temp_IDFinance=1時，為符合條件
    temp_IDFinance = 0
    if IDFinance:
        print(df_stock_code["股票代碼"].tolist()[0])
        endIDF = df_stock_code[df_stock_code['index'].isin([endIndex])]["成交量(千張)"].tolist()[0]
        print(startIndex,index)
        print(df_stock_code[df_stock_code['index'].isin([startIndex])]["成交量(千張)"].tolist())
        startIDF = df_stock_code[df_stock_code['index'].isin([startIndex])]["成交量(千張)"].tolist()[0]
        #成交變化量
        IDFRatio = (endIDF - startIDF)/startIDF

        if IDFinance == "增加":
            if IDFRatio > 0 :
                temp_IDFinance = 1
        elif IDFinance == "減少":
            if IDFRatio < 0 :
                temp_IDFinance = 1
        elif IDFinance == "增加/減少5%以上":
            if abs(IDFRatio) > 0.05:
                temp_IDFinance = 1
        elif IDFinance == "增加/減少10%以上":
            if abs(IDFRatio) > 0.1:
                temp_IDFinance = 1
        elif IDFinance == "增加/減少20%以上":
            if abs(IDFRatio) > 0.2:
                temp_IDFinance = 1
    else:
        temp_IDFinance = 1

    #當temp_quote_change=0時，為不符合條件;當temp_quote_change=1時，為符合條件
    temp_quote_change = 0
    if quote_change:
        endQC = df_stock_code[df_stock_code['index'].isin([endIndex])]["收盤價"].tolist()[0]
        startQC = df_stock_code[df_stock_code['index'].isin([startIndex])]["收盤價"].tolist()[0]

        #股價變化
        if endQC == "-" or startQC == "-":
            temp_quote_change = 0
        else:
            QCRatio = (float(endQC) - float(startQC)) / float(startQC)

            if quote_change == "上漲":
                if QCRatio > 0 :
                    temp_quote_change = 1
            elif quote_change == "下跌":
                if QCRatio < 0 :
                    temp_quote_change = 1
            elif quote_change == "上漲1%以上":
                if QCRatio > 0.01 :
                    temp_quote_change = 1
            elif quote_change == "上漲2%以上":
                if QCRatio > 0.02 :
                    temp_quote_change = 1
            elif quote_change == "上漲3%以上":
                if QCRatio > 0.03 :
                    temp_quote_change = 1
            elif quote_change == "下跌1%以上":
                if QCRatio < -0.01 :
                    temp_quote_change = 1
            elif quote_change == "下跌2%以上":
                if QCRatio < -0.02 :
                    temp_quote_change = 1
            elif quote_change == "下跌3%以上":
                if QCRatio < -0.03 :
                    temp_quote_change = 1
    else:
        temp_quote_change = 1

    if temp_quote_change == 1 and temp_IDFinance == 1:
        return df_stock_code['股票代碼'].tolist()[0], df_stock_code['股票名稱'].tolist()[0]
    else:
        return None, None
@csrf_exempt
def Search_stock_of_information(request):

    #獲取前端的傳送過來的數據
    IDFinance = request.POST.get("IDFinance")
    quote_change = request.POST.get("quote_change")
    datetimeStart = request.POST.get("datetimeStart")
    datetimeEnd = request.POST.get("datetimeEnd")
    time = request.POST.get("time")

    # 用DBAPI構建數據庫鏈接engine
    engine = create_engine("mysql+pymysql://trading:trading@localhost:3306/Job?charset=utf8")
    # 建立連接
    con = engine.connect()
    stock_codes =  pd.read_sql("SELECT * FROM stock_codes", con=engine)
    stock_codes = stock_codes['stock_code'].tolist()

    #存儲股票編碼和股票名稱
    list_stock_code = []
    list_stock_name = []

    #根據時間再挑選函數
    if datetimeStart and datetimeEnd :
        print("datetimeStart:", datetimeStart)
        print("datetimeEnd:", datetimeEnd)
        for i in stock_codes:
            df_stock_code = pd.read_sql("SELECT * FROM `" + str(i) + "`", con=engine)
            stock_code, stock_name = get_period(df_stock_code, datetimeStart, datetimeEnd, IDFinance, quote_change)
            if stock_code:
                list_stock_code.append(stock_code)
                list_stock_name.append(stock_name)
    else:
        if time == "過去1天":
            datetimeStart = "2023-03-31"
            datetimeEnd = "2023-03-30"
            for i in stock_codes:
                df_stock_code = pd.read_sql("SELECT * FROM `" + str(i) + "`", con=engine)
                stock_code, stock_name = get_period(df_stock_code, datetimeStart, datetimeEnd, IDFinance, quote_change)
                if stock_code:
                    list_stock_code.append(stock_code)
                    list_stock_name.append(stock_name)
        elif time == "過去5天":
            datetimeStart = "2023-03-31"
            datetimeEnd = "2023-03-26"
            for i in stock_codes:
                df_stock_code = pd.read_sql("SELECT * FROM `" + str(i) + "`", con=engine)
                stock_code, stock_name = get_period(df_stock_code, datetimeStart, datetimeEnd, IDFinance, quote_change)
                if stock_code:
                    list_stock_code.append(stock_code)
                    list_stock_name.append(stock_name)
        elif time == "過去10天":
            datetimeStart = "2023-03-31"
            datetimeEnd = "2023-03-21"
            for i in stock_codes:
                df_stock_code = pd.read_sql("SELECT * FROM `" + str(i) + "`", con=engine)
                stock_code, stock_name = get_period(df_stock_code, datetimeStart, datetimeEnd, IDFinance, quote_change)
                if stock_code:
                    list_stock_code.append(stock_code)
                    list_stock_name.append(stock_name)
    dict_all = {"stock_code" : list_stock_code, "stock_name": list_stock_name}
    data_all = DataFrame(dict_all)
    json_all = json.loads(data_all.to_json(orient='records', force_ascii=False))
    json_to_dict = {"Data": json_all}
    return JsonResponse(json_to_dict)
