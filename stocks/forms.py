from django import forms
from .patterns import candlestick_patterns


QUERY_OPTIONS=(
    ('#1', 'All Stocks'),
    ('#2','Nifty50'),
     ('#3','Nifty Metal'),
     ('#4','Bank Nifty'),
     ('#5','Nifty Auto'),
     ('#6','Nifty Pharma'),
     ('#7','Nifty FMCG'),
     ('#8','Nifty IT'),



)

PATTERN_OPTIONS= ( (k,v) for k,v in candlestick_patterns.items() )

class StockOptionForm(forms.Form):
   
    options=forms.ChoiceField(choices=QUERY_OPTIONS)

class StockSearchForm(forms.Form):
    date_from =forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    date_to =forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    
class Fooform(forms.Form):
    btn = forms.CharField()


class StockScannerForm(forms.Form):
    feilds=forms.ChoiceField(choices=PATTERN_OPTIONS)   