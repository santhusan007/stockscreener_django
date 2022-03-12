from django.conf import settings
import os
import datetime 
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
import pandas as pd
from .models import BroaderIndex,IndexPrice
from datetime import timedelta
from django.db.models.functions import Lag, Round
from django.db.models import F, Window, Q




NAME=settings.NAME
USER=settings.USER
PASSWORD=settings.PASSWORD
HOST=settings.HOST
ENGINE=settings.ENGINE

def data_base():
    while True:   
        try:
            conn=psycopg2.connect(host=HOST,database=NAME,user=USER,password=PASSWORD,
                                        cursor_factory=RealDictCursor)
            c=conn.cursor()
            #print("Database connection was sucessful")
            break
        except Exception as error:
            print("Not Connected")
            print("the error was",error)
            datetime.time.sleep(2)
    return c


def present_day():
    
    c=data_base()
    c.execute(""" SELECT max(date) as date from stock_price""")
    
    last_date=c.fetchone()
    latest_date=last_date['date']
    
    return latest_date


def prev_day(latest_d):
    c=data_base()
    i=1
    while True:      
        previous_date=latest_d-datetime.timedelta(days=i)
        c.execute("""select count(*) as countstock from stock_price where date = %s """,(previous_date,))
        stock_count=c.fetchone()
        latest_count=stock_count['countstock']
        if latest_count>0 :
            return previous_date
            break
        else:
            i+=1
# present_day=present_day()
# prev_day=prev_day(present_day)
# print(present_day)
# print(prev_day)

def stock_df(symbol):
    conn=psycopg2.connect(host='localhost',database='market',user='postgres',password='1234',
                                        cursor_factory=RealDictCursor)
    
    c=conn.cursor()
    c.execute ("""SELECT stock_price.date ,
            stocks.symbol,stock_price.close FROM stock_price JOIN stocks 
                ON stocks.id=stock_price.stock_id where symbol = %s order by date  """ ,(symbol,))
    stock=c.fetchall()
    stock_df=pd.DataFrame(stock,columns = ['date', 'symbol','close'])
    convert_dict = {'close':float}
    stock_df = stock_df.astype(convert_dict)
    stock_df['date']=pd.to_datetime(stock_df['date'])
    stock_df.set_index('date',inplace=True)
    stock_df['Close']=stock_df.close.pct_change()
    stock_df=stock_df['Close']
    return(stock_df)
    
#df=stock_df(symbol)
    # c=connection.cursor()
    # c.execute(""" SELECT id,symbol,company from stocks where symbol=%s""", (symbol,))
    # row = c.fetchone()
    
    # c.execute(""" SELECT * from stock_price where stock_id= %s """, (row[0],))

    # prices = dictfetchall(c)

    
    # stock_df = pd.DataFrame(prices, columns=[
    #                         'id', 'stock_id', 'open', 'high', 'low', 'close', 'volume', 'date'])

    # stock_df["open"] = stock_df["open"].astype(float)
    # stock_df["high"] = stock_df["high"].astype(float)
    # stock_df["low"] = stock_df["low"].astype(float)
    # stock_df["close"] = stock_df["close"].astype(float)
    # # stock_df["volume"] = stock_df["volume"].astype(float)
latest_day = present_day()
last_day = prev_day(latest_day)

def perodical_index(index,stocks,stockprice,indices,days,offset):
    date = latest_day-timedelta(days=days)
    indexstock = index.objects.filter(indices=indices).first()
    indexcount = stocks.objects.filter(broder_id=indexstock.id).count()
    indexstocks = stockprice.objects.all().select_related('stock')
    stocksectorprice = indexstocks.annotate(prev_close=Window(expression=Lag('close', offset=offset), partition_by=F("stock_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
        .filter(date__gte=date)\
        .filter(stock__broder_id=indexstock.id)\
        .order_by('-date', '-per_chan')[:indexcount]
    return date,indexstock,indexcount, indexstocks,stocksectorprice

def perodical_sector(index,stocks,stockprice,sec):
    sectorstock = index.objects.filter(sector=sec).first()
    sectorcount = stocks.objects.filter(sector=sectorstock.id).count()
    sectorstocks = stockprice.objects.all().select_related('stock')
    stocksectorprice =  sectorstocks.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("stock_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
        .filter(date__gte=last_day)\
        .filter(stock__sector_id=sectorstock.id)\
        .order_by('-date', '-per_chan')[:sectorcount]
    return sectorcount,sectorstock,stocksectorprice
    
def stocklist_sectorial(stocks,number):
    mystocks = stocks.objects.all().select_related('stock')
    qs=mystocks.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("stock_id"), order_by=F('date').asc(),))\
            .annotate(diff=F('close')-F('prev_close'))\
            .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
            .filter(stock__sectorial_index_id=number)\
            .filter(date__gte=last_day)
    return qs
