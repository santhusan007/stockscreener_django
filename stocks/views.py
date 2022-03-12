from django.db.models.functions import Lag, Round
from django.db.models import F, Window, Q
from .helper import present_day, prev_day
import talib
from datetime import timedelta
from plotly.graph_objs import Scatter
from plotly.offline import plot
from .patterns import candlestick_patterns
from django.shortcuts import render
from .models import (BroaderIndex, Sector, SectorialIndex, Stocks,StockPrice, IndexPrice)
from django.db import connection
from .forms import StockOptionForm, StockScannerForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import pandas as pd
import quantstats as qs
from .helper import perodical_index,perodical_sector,stocklist_sectorial
qs.extend_pandas()


latest_day = present_day()
last_day = prev_day(latest_day)
# Create your views here.


def StockListView(request):
    form = StockOptionForm(request.POST or None)
    options = request.POST.get("options")
    # print(form)
    mystocks = StockPrice.objects.all().select_related('stock')

    if options == '#2':

        qs = mystocks.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("stock_id"), order_by=F('date').asc(),))\
            .annotate(diff=F('close')-F('prev_close'))\
            .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
            .filter(stock__broder_id=1)\
            .filter(date__gte=last_day)


    elif options == '#3':
        qs = stocklist_sectorial(StockPrice,7)
              
    elif options == '#4':
        qs = stocklist_sectorial(StockPrice,3)
    
    elif options == '#5':
        qs = stocklist_sectorial(StockPrice,2)
    
    elif options == '#6':
        qs = stocklist_sectorial(StockPrice,8)
    
    elif options == '#7':
        qs = stocklist_sectorial(StockPrice,1)
    
    elif options == '#8':
        qs = stocklist_sectorial(StockPrice,5)
       
    else:

        qs = mystocks.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("stock_id"), order_by=F('date').asc(),))\
            .annotate(diff=F('close')-F('prev_close'))\
            .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
            .filter(date__gte=last_day)

    stocks = qs
    broders = BroaderIndex.objects.all().order_by('indices')
    sectors = Sector.objects.all().order_by('sector')
    sector_index = SectorialIndex.objects.all().order_by('sector')

    context = {'stocks': stocks, 'form': form, 'sectors': sectors,
               'broders': broders, 'sector_index': sector_index}

    return render(request, "stocks/stocks_list.html", context)


def stock_detail(request, symbol):

    stock = Stocks.objects.filter(symbol=symbol).first()
    stocks = StockPrice.objects.filter(
        stock_id=stock.id).order_by('-date').all()
    page = request.GET.get('page', 1)
    paginator = Paginator(stocks, 15)

    # get the page parameter from the query string
    # if page parameter is available get() method will return empty string ''
    # page = request.GET.get('page')
    try:
        # create Page object for the given page
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # if page parameter in the query string is not available, return the first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # if the value of the page parameter exceeds num_pages then return the last page
        page_obj = paginator.page(paginator.num_pages)

    context = {'stock': stock, 'page_obj': page_obj, 'stocks': stocks}

    return render(request, 'stocks/stock_detail.html', context)


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def stock_return(request,company):

    stock = Stocks.objects.filter(company=company).first()
    prices = StockPrice.objects.filter(stock_id=stock.id).order_by('date').all()
    queryset = prices.values_list('id', 'stock_id', 'close', 'date')
    stock_df = pd.DataFrame(list(queryset), columns=[
                            'id', 'stock_id', 'close', 'date'])
    convert_dict = {'close': float}
    stock_df = stock_df.astype(convert_dict)
    stock_df['date'] = pd.to_datetime(stock_df['date'])
    stock_df.set_index('date', inplace=True)
    stock_df['Close'] = stock_df.close.pct_change()
    stock_df = stock_df['Close']

    qs.reports.html(stock_df, title=f'{company}_performance',
                    output=r'D:\pyhton\stock_screeneer_django\stocks\templates\stocks\stock_return.html')

    return render(request, 'stocks/stock_return.html')


def stock_scanner(request):
    form = StockScannerForm(request.POST or None)
    options = request.POST.get("feilds", None)
    # print(options)
    # options= 'CDLENGULFING'
    latest_day = present_day()
    stocks = {}
    # stocks_company={}
    symbol = []

    if options:
        main_df = pd.read_sql_query("""SELECT stock_price.date,stock_price.stock_id , stocks.symbol,stocks.company,stock_price.open,stock_price.high,
				stock_price.low,stock_price.close FROM stock_price JOIN stocks
                ON stocks.id=stock_price.stock_id where date between (select (SELECT max(date) from stock_price) + INTERVAL '-10 day')
                 and (SELECT max(date) from stock_price) """, connection)

        final_df = pd.DataFrame()
        # prefinal_df=pd.DataFrame()
        for index, ticker in enumerate(main_df['symbol'].unique()):
            # stocks_company[ticker]=main_df.loc[index,'company']
            stocks[ticker] = main_df.loc[index, 'company']
            temp = main_df.loc[index, 'symbol']
            # print(temp)
            symbol.append(temp)
            df = main_df.loc[main_df['symbol'] ==
                             ticker][['open', 'high', 'low', 'close']]

            pattern_fun = getattr(talib, options)
            try:
                df['result'] = pattern_fun(
                    df['open'], df['high'], df['low'], df['close'])
                # final_df=final_df.append(df)
                final_df = pd.concat([final_df, df], axis=0)
                # print(final_df)
                # print(prefinal_df)

            except Exception as e:
                print("select a symbol")

        main_df = pd.merge(main_df, final_df)

        day_df = main_df.copy()[main_df['date'] == latest_day]
        # print(day_df)

        day_df.loc[day_df['result'] > 0, 'pattern'] = 'bullish'
        day_df.loc[day_df['result'] < 0, 'pattern'] = 'bearish'
        day_df.loc[day_df['result'] == 0, 'pattern'] = None
        day_df.reset_index(inplace=True)
        day_df.drop(columns='index', inplace=True)
        for i, symbol in enumerate(day_df.symbol):
            stocks[symbol] = day_df.loc[i, 'pattern']

        # print(stocks)

    context = {"form": form, "options": options, "stocks": stocks}

    return render(request, 'stocks/stocks_scanner.html', context)


def heatmap_sector(request,sector):
    # mysector=perodical_sector(SectorialIndex,Stocks,StockPrice,sector)
    # context = {"stocksectorprice": mysector[2],
    #            "sectorstock": mysector[1]}



    sectorstock = SectorialIndex.objects.filter(sector=sector).first()
    sectorcount = Stocks.objects.filter(sectorial_index=sectorstock.id).count()
    sectorstocks = StockPrice.objects.all().select_related('stock')
    stocksectorprice = sectorstocks.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("stock_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
        .filter(date__gte=last_day)\
        .filter(stock__sectorial_index_id=sectorstock.id)\
        .order_by('-date', '-per_chan')[:sectorcount]

    context = {"stocksectorprice": stocksectorprice,
               "sectorstock": sectorstock, "sectorcount": sectorcount}
    return render(request, 'stocks/sector_heatmap.html', context)


def heatmap_stocks(request, sector):

    mysector=perodical_sector(Sector,Stocks,StockPrice,sector)
    context = {"stocksectorprice": mysector[2],
               "sectorstock": mysector[1]}
    return render(request, 'stocks/sector_stock_heatmap.html', context)


def heatmap_index(request, indices):
    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=1,offset=1)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}
    return render(request, 'stocks/heatmap_index.html', context)


def oneweekindex(request, indices):
    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=10,offset=6)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}
    return render(request, 'stocks/heatmap_index_1week.html', context)

def onemonthindex(request, indices):
    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=35,offset=23)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}
    return render(request, 'stocks/heatmap_index_1month.html', context)


def threemonthindex(request, indices):

    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=105,offset=68)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}
    return render(request, 'stocks/heatmap_index_3month.html', context)


def sixmonthindex(request, indices):
    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=200,offset=135)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}
    return render(request, 'stocks/heatmap_index_6month.html', context)


def oneyearindex(request, indices):
    myindex=perodical_index(BroaderIndex,Stocks,StockPrice,indices,days=400,offset=260)
    context = {"stocksectorprice": myindex[4],
               "sectorstock": myindex[1], "indexcount": myindex[2]}

    return render(request, 'stocks/heatmap_index_1year.html', context)


def index_sector(request):

    myIndex = IndexPrice.objects.all().select_related(
        'broader').filter(Q(broader__isnull=False))
    indexprice = myIndex.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("broader_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
        .filter(date__gte=last_day)

    mySector = IndexPrice.objects.all().select_related(
        'sectorial').filter(Q(sectorial__isnull=False))
    sectorprice = mySector.annotate(prev_close=Window(expression=Lag('close'), partition_by=F("sectorial_id"), order_by=F('date').asc(),))\
        .annotate(diff=F('close')-F('prev_close'))\
        .annotate(per_chan=Round(F('diff')/F('close')*100, 2))\
        .filter(date__gte=last_day)

    context = {"indexprice": indexprice, "sectorprice": sectorprice}
    # print(last_day,latest_day)
    return render(request, 'stocks/index_sector.html', context)


def index(request, indices):
    main_index = BroaderIndex.objects.filter(indices=indices).first()
    index_price = IndexPrice.objects.filter(
        broader_id=main_index.id).order_by('-date').all()
   
    context = {'main_index': main_index, 'index_price': index_price}

    return render(request, 'stocks/broader_index.html', context)


def sector(request, sector):  

    sector_index1 = SectorialIndex.objects.filter(sector=sector).first()
    sector_price = IndexPrice.objects.filter(
        sectorial_id=sector_index1.id).order_by('-date').all()
    context = {'sector_index1': sector_index1, 'sector_price': sector_price}
    return render(request, 'stocks/sector_index.html', context)


def chart(request):
    x_data = [0, 1, 2, 3]
    y_data = [x**2 for x in x_data]
    plot_div = plot([Scatter(x=x_data, y=y_data,
                             mode='lines', name='test',
                             opacity=0.8, marker_color='green')],
                    output_type='div', show_link=False, link_text="")
    return render(request, "stocks/index1.html", context={'plot_div': plot_div})


