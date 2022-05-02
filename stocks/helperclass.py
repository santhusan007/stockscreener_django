from django.conf import settings
import os
import datetime
from matplotlib import offsetbox
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
import pandas as pd
from .models import BroaderIndex, StockPrice
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


class StockFilters:
    
    def __init__(self,stocks,offset,days):
        self.stocks=stocks
        self.offset=offset
        self.days=days


    def StockTableFilter(self):
        
        """function to filter the stock / index price query set with annotate the privios close,
        percentage change with resepect to previous day."""
        date = dateFilter(self.days)
        stocks=self.stocks.objects.all().select_related('stock')
        qs=(
        stocks
        .annotate(prev_close=Window(expression=Lag('close', offset=self.offset), 
                partition_by=F("stock_id"), order_by=F('date').asc(),))
        .annotate(diff=F('close')-F('prev_close'))
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))
        .filter(date__gte=date)
        )
        return qs   

        
    def perodical_index(self,index,indices):

        indexstock = index.objects.filter(indices=indices).first()
        indexcount = self.stocks.objects.filter(broder_id=indexstock.id).count()
        qs =StockFilters(self.stocks,self.offset,self.days)
        stocksectorprice=(
            
                        qs.filter(stock__broder_id=indexstock.id)
                        .order_by('-date', '-per_chan')[:indexcount]
                )
        return  indexstock, indexcount ,stocksectorprice            

def fivedays_down(stocks,days):
    date = dateFilter(days)
    stocks=stocks.objects.all().select_related('stock')
    qs=(stocks.annotate(prev_close=Window(expression=Lag('close', offset=1),
                         partition_by=F("stock_id"), order_by=F('date').asc(),))
        .annotate(twodaybefore_close=Window(expression=Lag('close', offset=2),
                         partition_by=F("stock_id"), order_by=F('date').asc(),))
        .annotate(threedaybefore_close=Window(expression=Lag('close', offset=3),
                         partition_by=F("stock_id"), order_by=F('date').asc(),))
        .annotate(fourdaybefore_close=Window(expression=Lag('close', offset=4),
                         partition_by=F("stock_id"), order_by=F('date').asc(),))
        .annotate(diff=F('close')-F('fourdaybefore_close'))
        .annotate(fivedays_return=Round(F('diff')/F('fourdaybefore_close')*100, 2))
        .filter(date__gte=date)
        .filter(Q(prev_close__lte =F('close')) 
                    & Q(twodaybefore_close__lte=F('prev_close')) 
                    & Q(threedaybefore_close__lte=F('twodaybefore_close')) 
                    & Q(fourdaybefore_close__lte=F('threedaybefore_close')))

    )
    return qs





