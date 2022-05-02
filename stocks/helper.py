from django.conf import settings
import os
import datetime
from matplotlib import offsetbox
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
import pandas as pd
from .models import BroaderIndex, StockPrice,Stocks
from datetime import timedelta
from django.db.models.functions import Lag, Round
from django.db.models import F, Window, Q,Max,Min,Count


NAME = settings.NAME
USER = settings.USER
PASSWORD = settings.PASSWORD
HOST = settings.HOST
ENGINE = settings.ENGINE


def data_base():
    while True:
        try:
            conn = psycopg2.connect(host=HOST, database=NAME, user=USER, password=PASSWORD,
                                    cursor_factory=RealDictCursor)
            c = conn.cursor()
            #print("Database connection was sucessful")
            break
        except Exception as error:
            print("Not Connected")
            print("the error was", error)
            datetime.time.sleep(2)
    return c


def present_day():
    c = data_base()
    c.execute(""" SELECT max(date) as date from stock_price""")
    last_date = c.fetchone()
    latest_date = last_date['date']
    return latest_date


def prev_day(latest_d):
    c = data_base()
    i = 1
    while True:
        previous_date = latest_d-datetime.timedelta(days=i)
        c.execute(
            """select count(*) as countstock from stock_price where date = %s """, (previous_date,))
        stock_count = c.fetchone()
        latest_count = stock_count['countstock']
        if latest_count > 0:
            return previous_date
            break
        else:
            i += 1
latest_day = present_day()
last_day = prev_day(latest_day)


def dateFilter(days):
    if days==1:
        return last_day
    return latest_day-timedelta(days=days)
        

def mystocklist(stocks,offset,days):
        """function to filter the stock / index price query set with annotate the privios close,
        percentage change with resepect to previous day."""
        date = dateFilter(days)
        stocklist=stocks.objects.all().select_related('stock')
        qs=stocklist.annotate(prev_close=Window(expression=Lag('close', offset=offset), partition_by=F("stock_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('prev_close')*100, 2))\
        .filter(date__gte=date)
        return qs

def perodical_index(index, stocks, indices, days, offset):
    indexstock = index.objects.filter(indices=indices).first()
    indexcount = stocks.objects.filter(broder_id=indexstock.id).count()
    qs =mystocklist(StockPrice,offset,days)
    stocksectorprice=qs.filter(stock__broder_id=indexstock.id)\
        .order_by('-date', '-per_chan')[:indexcount]    
    return  indexstock, indexcount ,stocksectorprice


def perodical_sector(index, stocks,sec,days, offset):
    sectorstock = index.objects.filter(sector=sec).first()
    sectorcount = stocks.objects.filter(sector=sectorstock.id).count()
    qs =mystocklist(StockPrice,offset,days)
    stocksectorprice=qs.filter(stock__sector_id=sectorstock.id)\
        .order_by('-date', '-per_chan')[:sectorcount]
    return sectorcount, sectorstock, stocksectorprice

def perodical_mainsector(index, stocks,sec,days,offset):
    sectorstock = index.objects.filter(sector=sec).first()
    sectorcount = stocks.objects.filter(sectorial_index=sectorstock.id).count()
    qs =mystocklist(StockPrice,offset,days)
    stocksectorprice=qs.filter(stock__sectorial_index_id=sectorstock.id)\
        .order_by('-date', '-per_chan')[:sectorcount]
    return sectorcount, sectorstock, stocksectorprice

def index_sector_price(index,id):
    indexprice = index.annotate(prev_close=Window(expression=Lag('close'), partition_by=F(id), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('prev_close')*100, 2))\
        .filter(date__gte=last_day)\
        .order_by('-per_chan')
    return indexprice


def stocklist_sectorial(number,offset=1,days=1):
    mystocks = mystocklist(StockPrice,offset,days)
    qs = mystocks.filter(stock__sectorial_index_id=number).order_by('-date','-per_chan')
    return qs

def broader_index_deatils(number,offset=1,days=1):
    mystocks = mystocklist(StockPrice,offset,days)
    qs = mystocks.filter(stock__broder_id=number).order_by('-date','-per_chan')#[:bordercount]
    return qs

def mainpage_details(offset=1,days=1):
    mystocks = mystocklist(StockPrice,offset,days)
    qs = mystocks.order_by('-date','-per_chan')
    return qs


def mainpage_dropdown(option):
    options = {
        '#1':mainpage_details(),
        '#2': broader_index_deatils(1),
        '#3': broader_index_deatils(3),
        '#4': broader_index_deatils(4),
        '#5': stocklist_sectorial(7),
        '#6': stocklist_sectorial(3),
        '#7': stocklist_sectorial(2),
        '#8': stocklist_sectorial(8),
        '#9': stocklist_sectorial(1),
        '#10': stocklist_sectorial(5),

    }
    if option in options:
        qs = options[option]
        return qs


def fivedaydown():
    sqlquery="""
    SELECT  id,stock_id,symbol,close,Prev_close,fivedaysago,fivedays_Rtn from
                (
                SELECT stocks.ID,stocks.symbol,close ,date,stock_id,
                lag(close) over (PARTITION BY stock_id ORDER BY date) AS Prev_close,
                lag(close,4) over (PARTITION BY stock_id ORDER BY date) as fivedaysago,
                round((close-lag(close,4) over (PARTITION BY stock_id ORDER BY date) )/
                lag(close,4) over (PARTITION BY stock_id ORDER BY date)*100,2) as fivedays_Rtn,
                CASE 
                        WHEN 
                        lag(close) over (PARTITION BY stock_id ORDER BY date) > close AND
                        lag(close,2) over (PARTITION BY stock_id ORDER BY date) > lag(close) over (PARTITION BY stock_id ORDER BY date) AND
                        lag(close,3) over (PARTITION BY stock_id ORDER BY date) > lag(close,2) over (PARTITION BY stock_id ORDER BY date) AND
                        lag(close,4) over (PARTITION BY stock_id ORDER BY date) > lag(close,3) over (PARTITION BY stock_id ORDER BY date) 
                        
                        
                        THEN 'yes' ELSE NULL 
                END gap
                        
                FROM
                stocks JOIN stock_price ON stocks.ID = stock_price.stock_id
                            
                WHERE date BETWEEN (select date(max(date)+ INTERVAL'-10 day') FROM stock_price)
                AND (select max(date) FROM stock_price)) as foo WHERE gap='yes' AND date=(select max(date) FROM stock_price)
				ORDER BY 5 limit 5
    
    """
    qs=StockPrice.objects.raw(sqlquery)
    return qs

def fivedayup():
    sqlquery="""
        SELECT id,stock_id,symbol,close,Prev_close,fivedaysago,fivedays_Rtn from (
                SELECT stocks.ID,stock_id,stocks.symbol,close ,date,
                lag(close) over (PARTITION BY stock_id ORDER BY date) AS Prev_close,
                lag(close,4) over (PARTITION BY stock_id ORDER BY date) as fivedaysago,
                round((close-lag(close,4) over (PARTITION BY stock_id ORDER BY date) )/
                lag(close,4) over (PARTITION BY stock_id ORDER BY date)*100,2) as fivedays_Rtn,
                CASE 
                        WHEN 
                        lag(close) over (PARTITION BY stock_id ORDER BY date) < close AND
                        lag(close,2) over (PARTITION BY stock_id ORDER BY date) < lag(close) over (PARTITION BY stock_id ORDER BY date) AND
                        lag(close,3) over (PARTITION BY stock_id ORDER BY date) < lag(close,2) over (PARTITION BY stock_id ORDER BY date) AND
                        lag(close,4) over (PARTITION BY stock_id ORDER BY date) < lag(close,3) over (PARTITION BY stock_id ORDER BY date) 
                        
                        
                        THEN 'yes' ELSE NULL 
                END gap
                        
                    FROM
                        stocks JOIN stock_price ON stocks.id = stock_price.stock_id
                            
                WHERE date BETWEEN (select date(max(date) +INTERVAL '-10 day') FROM stock_price)
                AND (select max(date) FROM stock_price)) as bar WHERE gap='yes' AND date=(select max(date) FROM stock_price) ORDER BY 5 
                 desc limit 5  

    """

    qs=StockPrice.objects.raw(sqlquery)
    return qs
