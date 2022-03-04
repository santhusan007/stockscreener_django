from django.db import models

# Create your models here.

class BroaderIndex(models.Model):
    id = models.IntegerField(primary_key=True)
    indices = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'broader_index'

class Sector(models.Model):
    id = models.IntegerField(primary_key=True)
    sector = models.CharField(max_length=100)

    def __str__(self):
        return self.sector

    class Meta:
        managed = False
        db_table = 'sector'


class SectorialIndex(models.Model):
    id = models.IntegerField(primary_key=True)
    sector = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)

    def __str__(self):
        return self.sector

    class Meta:
        managed = False
        db_table = 'sectorial_index'


class Stocks(models.Model):
    id = models.IntegerField(primary_key=True)
    symbol = models.CharField(unique=True, max_length=100)
    company = models.CharField(max_length=200)
    sector = models.ForeignKey(Sector, models.DO_NOTHING, blank=True, null=True)
    broder = models.ForeignKey(BroaderIndex, models.DO_NOTHING, blank=True, null=True)
    sectorial_index = models.ForeignKey(SectorialIndex, models.DO_NOTHING, db_column='sectorial_index', blank=True, null=True)

    def __str__(self):
        return self.symbol


    class Meta:
        managed = False
        db_table = 'stocks'


class Commodities(models.Model):
    id = models.IntegerField(primary_key=True)
    com_sym = models.TextField()
    com_description = models.TextField()

    def __str__(self):
        return self.com_sym

    class Meta:
        managed = False
        db_table = 'commodities'


class CuLmeCsp(models.Model):
    id = models.IntegerField(primary_key=True)
    com = models.ForeignKey(Commodities, models.DO_NOTHING)
    date = models.DateField()
    rate = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.com}"

    class Meta:
        managed = False
        db_table = 'cu_lme_csp'


class Currency(models.Model):
    id = models.IntegerField(primary_key=True)
    cur_symbol = models.TextField(unique=True)
    cus_des = models.TextField()

    def __str__(self):
        return self.cur_symbol

    class Meta:
        managed = False
        db_table = 'currency'


class RbiExchange(models.Model):
    id = models.IntegerField(primary_key=True)
    date = models.DateField()
    cur = models.ForeignKey(Currency, models.DO_NOTHING)
    rate = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.cur}"
    
    class Meta:
        managed = False
        db_table = 'rbi_exchange'
        
class FoStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    stk = models.ForeignKey(Stocks, models.DO_NOTHING)
    fo_status = models.IntegerField()

    def __str__(self):
        return f"{self.stk}"

    class Meta:
        managed = False
        db_table = 'fo_status'


class IndexPrice(models.Model):
    id = models.IntegerField(primary_key=True)
    broader = models.ForeignKey(BroaderIndex, models.DO_NOTHING, blank=True, null=True)
    sectorial = models.ForeignKey(SectorialIndex, models.DO_NOTHING, blank=True, null=True)
    date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        managed = False
        db_table = 'index_price'       


class StockPrice(models.Model):
    id = models.IntegerField(primary_key=True)
    stock = models.ForeignKey(Stocks, models.DO_NOTHING)
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.stock}"

    class Meta:
        managed = False
        db_table = 'stock_price'
    
   

