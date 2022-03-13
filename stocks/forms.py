from django import forms
from .patterns import candlestick_patterns


QUERY_OPTIONS=(
    ('#1', 'All Stocks'),
    ('#2','Nifty 50'),
    ('#3','Midcap 100'),
    ('#4','Smallcap 100'),
     ('#5','Nifty Metal'),
     ('#6','Bank Nifty'),
     ('#7','Nifty Auto'),
     ('#8','Nifty Pharma'),
     ('#9','Nifty FMCG'),
     ('#10','Nifty IT'),

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