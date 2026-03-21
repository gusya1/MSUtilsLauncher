

from django import forms
from django.forms import formset_factory


class DateChooseForm(forms.Form):
    date = forms.DateField(label='Выберете дату', widget=forms.DateInput(attrs={'type': 'date'}))

class OrderForm(forms.Form):
    name = forms.CharField(label='Номер', disabled=True)
    address = forms.CharField(label='Адрес', widget=forms.Textarea(attrs={'rows': 3}))
    start_time = forms.TimeField(label='Ожидают с', widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    end_time = forms.TimeField(label='по', widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    weight = forms.IntegerField(label='Вес (кг)')