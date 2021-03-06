from django.db.models import  Q
import talib
from plotly.graph_objs import Scatter
from plotly.offline import plot
from django.shortcuts import render
from .models import (BroaderIndex, Sector, SectorialIndex,
                     Stocks, StockPrice, IndexPrice,RbiExchange, Currency,CuLmeCsp)
from django.db import connection
from .forms import StockOptionForm, StockScannerForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import pandas as pd
import quantstats as qs
from .helper import (perodical_index, perodical_sector,present_day, prev_day,
                     index_sector_price, mainpage_dropdown,
                     mainpage_details,perodical_mainsector,bearishEngulf,bullishEngulf,
                     volumebuzzers,fostocks,currencylist,copperdetail,yearlyhighlow)

qs.extend_pandas()

latest_day = present_day()
last_day = prev_day(latest_day)
# Create your views here.

def StockListView(request):
    form = StockOptionForm(request.POST or None)
    options = request.POST.get("options")
    #dates=request.POST.get("dateselection")
    # print(form)
    
    if options :
        qs = mainpage_dropdown(options)        
    else:
        qs = mainpage_details(offset=1,days=1)
        # if else replace with dictionery

    
    broders = BroaderIndex.objects.all().order_by('indices')
    sectors = Sector.objects.all().order_by('sector')
    sector_index = SectorialIndex.objects.all().order_by('sector')
    index_price=IndexPrice.objects.filter(date=latest_day)

    context = {'stocks': qs, 'form': form, 'sectors': sectors,
               'broders': broders, 'sector_index': sector_index,'latest_day':latest_day ,"index_price":index_price}

    return render(request, "stocks/stocks_list.html", context)


def stock_detail(request,symbol):

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


def stock_return(request, company):

    stock = Stocks.objects.filter(company=company).first()
    prices = StockPrice.objects.filter(
        stock_id=stock.id).order_by('date').all()
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
        main_df = pd.read_sql_query("""select * from stock_scanner """, connection)

        final_df = pd.DataFrame()
        # prefinal_df=pd.DataFrame()
        for index, ticker in enumerate(main_df['symbol'].unique()):
            # stocks_company[ticker]=main_df.loc[index,'company']
            stocks[ticker] = main_df.loc[index, 'company']
            temp = main_df.loc[index, 'symbol']
            # print(temp)
            symbol.append(temp)
            df = main_df.loc[main_df['symbol'] ==ticker][['open', 'high', 'low', 'close']]

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


def heatmap_sector(request, sector):
    heatmapdict= {"1day":perodical_mainsector(SectorialIndex, Stocks, sector, days=1, offset=1),
                  "1week":perodical_mainsector(SectorialIndex, Stocks, sector, days=25, offset=6),
                "1month":perodical_mainsector(SectorialIndex, Stocks, sector, days=40, offset=23),
                "3month":perodical_mainsector(SectorialIndex, Stocks, sector, days=120, offset=68),
                "6month":perodical_mainsector(SectorialIndex, Stocks, sector, days=240, offset=135),
                "1year":perodical_mainsector(SectorialIndex, Stocks, sector, days=440, offset=260)                
                    }
    
    if request.method=='POST':
        heatmap=request.POST.get("heatmap")
        mysector=heatmapdict[heatmap]
          
        context = {"stocksectorprice": mysector[2],
                "sectorstock": mysector[1],"heatmap":heatmap}
        return render(request, 'stocks/sector_heatmap.html', context)

    else:
        mysector = perodical_mainsector(SectorialIndex, Stocks, sector, days=1, offset=1)
        
        context = {"stocksectorprice": mysector[2],
                "sectorstock": mysector[1]}
        return render(request, 'stocks/sector_heatmap.html', context)


def heatmap_stocks(request, sector):
    heatmapdict= {"1day":perodical_sector(Sector, Stocks, sector, days=1, offset=1),
                  "1week":perodical_sector(Sector, Stocks, sector, days=25, offset=6),
                "1month":perodical_sector(Sector, Stocks, sector, days=40, offset=23),
                "3month":perodical_sector(Sector, Stocks, sector, days=120, offset=68),
                "6month":perodical_sector(Sector, Stocks, sector, days=240, offset=135),
                "1year":perodical_sector(Sector, Stocks, sector, days=420, offset=260)                
                    }
    if request.method=='POST':
        heatmap=request.POST.get("heatmap")
        print(heatmap)
        mysector=heatmapdict[heatmap]           
           
        context = {"stocksectorprice": mysector[2],
                "sectorstock": mysector[1],"heatmap":heatmap}
        return render(request, 'stocks/sector_stock_heatmap.html', context)
    else:
        mysector = perodical_sector(Sector, Stocks, sector, days=1, offset=1)
        context = {"stocksectorprice": mysector[2],
               "sectorstock": mysector[1]}
        return render(request, 'stocks/sector_stock_heatmap.html', context)


def heatmap_index(request, indices):
    heatmapdict= {"1day":perodical_index(BroaderIndex, Stocks, indices, days=1, offset=1),
                  "1week":perodical_index(BroaderIndex, Stocks, indices, days=25, offset=6),
                "1month":perodical_index(BroaderIndex, Stocks, indices, days=40, offset=23),
                "3month":perodical_index(BroaderIndex, Stocks, indices, days=125, offset=68),
                "6month":perodical_index(BroaderIndex, Stocks, indices, days=240, offset=135),
                "1year":perodical_index(BroaderIndex, Stocks, indices, days=420, offset=260)                
                    }

    if request.method=='POST':
        heatmap=request.POST.get("heatmap")
        myindex=heatmapdict[heatmap]
        context = {"stocksectorprice": myindex[2],
               "sectorstock": myindex[0], "indexcount": myindex[1],"heatmap":heatmap}
        return render(request, 'stocks/heatmap_index.html', context)
                
    else:
        myindex = perodical_index(BroaderIndex, Stocks, indices, days=1, offset=1)
            
        context = {"stocksectorprice": myindex[2],
               "sectorstock": myindex[0], "indexcount": myindex[1]}
        return render(request, 'stocks/heatmap_index.html', context)
 
def index_sector(request):

    myIndex = IndexPrice.objects.all().select_related(
        'broader').filter(Q(broader__isnull=False))
    indexprice = index_sector_price(myIndex, "broader_id")

    mySector = IndexPrice.objects.all().select_related(
        'sectorial').filter(Q(sectorial__isnull=False))
    sectorprice = index_sector_price(mySector, "sectorial_id")

    context = {"indexprice": indexprice, "sectorprice": sectorprice}
    
    return render(request, 'stocks/index_sector.html', context)


def index(request, sector):
    main_index = BroaderIndex.objects.filter(indices=sector).first()
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

def engulfing(request):
    # bearish=bearishEngulf()
    # bullish=bullishEngulf()
    # volbuz=volumebuzzers()
    context={"bearish":bearishEngulf,"bullish":bullishEngulf,"vol":volumebuzzers,'yearhighlow':yearlyhighlow}
    return render(request,"stocks/engulfing.html",context)

def fnostocks(request):

    fo = fostocks(StockPrice,1,1)
    context={"fostocks":fo,"latest_day":present_day,}    
    return render(request,"stocks/fostocks.html",context)


def fnoheatmap(request):
    heatmapdict={"1day":fostocks(StockPrice,  days=1, offset=1),
                        "1week":fostocks(StockPrice, days=25, offset=6),
                        "1month":fostocks(StockPrice,days=40, offset=23),
                        "3month":fostocks(StockPrice, days=120, offset=68),
                        "6month":fostocks(StockPrice,days=240, offset=135),
                        "1year":fostocks(StockPrice, days=420, offset=260)}
    if request.method=='POST':
        heatmap=request.POST.get("heatmap")
        print(heatmap)
        fo=heatmapdict[heatmap]
        context={"fostocks":fo,"latest_day":present_day,"heatmap":heatmap}  
        return render(request,"stocks/foheatmap.html",context)       
    else:
        fo = fostocks(StockPrice, days=1, offset=1)
        context={"fostocks":fo,"latest_day":present_day}  
        return render(request,"stocks/foheatmap.html",context) 

def currencyiew(request):
    currencydetail=currencylist(RbiExchange,offset=1,days=1)
    context={"currencydetail":currencydetail,"latest_day":present_day}
    return render(request,"stocks/currencylist.html",context) 

def currency_detail(request,symbol):

    currency = Currency.objects.filter(cur_symbol=symbol).first()
    currencydetail = RbiExchange.objects.filter(cur_id=currency.id).order_by('-date').all()

    context={"currency":currency,"currencydetail":currencydetail}
    return render(request, 'stocks/currency_detail.html', context)

def copper_detail(request):
    copperlist= copperdetail(CuLmeCsp)
    page = request.GET.get('page', 1)
    paginator = Paginator(copperlist, 25)   

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

    context={"copperlist":copperlist,"page_obj":page_obj,"latest_day":latest_day}
    return render(request, 'stocks/copper_detail.html', context)

def visualTableu(request):

    return render(request, 'stocks/visual.html')