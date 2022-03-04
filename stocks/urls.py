from django.urls import path
from .views import *
from .import views

app_name='stocks'

urlpatterns = [
    path('',views.StockListView,name='stock-list'),
    path('stocks/index_sector',views.index_sector,name='index-sector'),
    path('stocks/scanner/',views.stock_scanner,name='stock-scanner'),
    path('stocks/chart/',views.chart,name='stock-chart'),
    path('stocks/<str:symbol>/',views.stock_detail,name='stock-detail'),
    path('stocks/return/<str:company>/',views.stock_return,name='stock-return'),
    path('stocks/sector_heatmap/<str:sector>/',views.heatmap_sector,name='sector-heatmap'),
    path('stocks/sector_stock_heatmap/<str:sector>/',views.heatmap_stocks,name='stock-heatmap'),
    path('stocks/index/<str:indices>/',views.heatmap_index,name='index-heatmap'),
    path('stocks/index_price/<str:indices>/',views.index,name='index-price'),
    path('stocks/sector_price/<str:sector>/',views.sector,name='sector-price'),
    path('stocks/oneweekindex/<str:indices>/',views.oneweekindex,name='oneweekindex'),
    path('stocks/onemonthindex/<str:indices>/',views.onemonthindex,name='onemonthindex'),
    path('stocks/threemonthindex/<str:indices>/',views.threemonthindex,name='threemonthindex'),
    path('stocks/sixmonthindex/<str:indices>/',views.sixmonthindex,name='sixmonthindex'),
    path('stocks/oneyearindex/<str:indices>/',views.oneyearindex,name='oneyearindex'),


    #path('stocks/view',views.stock_view,name='stock-view'),
]
