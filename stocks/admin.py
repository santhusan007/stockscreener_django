from django.contrib import admin
from .models import (
                    BroaderIndex, Sector,SectorialIndex,Stocks,FoStatus,Commodities,
                    CuLmeCsp,Currency,RbiExchange,StockPrice,IndexPrice
                    )
                    
admin.site.register(BroaderIndex)
admin.site.register(Sector)
admin.site.register(SectorialIndex)
admin.site.register(Stocks)
admin.site.register(FoStatus)
admin.site.register(CuLmeCsp)
admin.site.register(Currency)
admin.site.register(RbiExchange)
admin.site.register(StockPrice)
admin.site.register(IndexPrice)

