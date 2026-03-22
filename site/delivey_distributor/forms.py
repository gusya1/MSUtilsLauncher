
import logging
import re

from django import forms


from yandex_geocoder.geocoder import Geocoder
from yandex_geocoder.models import Location

from .core.data_structure import Point
from .models import Courier


logger = logging.getLogger("delivey_distributor")


def make_point_by_location(location: Location):
    return Point(longitude=location.longitude, latitude=location.latitude)

class DateChooseForm(forms.Form):
    date = forms.DateField(label='Выберете дату', widget=forms.DateInput(attrs={'type': 'date'}))

class OrderForm(forms.Form):
    name = forms.CharField(label='Номер')
    address = forms.CharField(label='Адрес', widget=forms.Textarea(attrs={'rows': 3}))
    start_time = forms.TimeField(label='Ожидают с', widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    end_time = forms.TimeField(label='по', widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    weight = forms.IntegerField(label='Вес (кг)')

    def __init__(self, *args, geocoder: Geocoder, **kwargs):
        self.geocoder = geocoder
        super().__init__(*args, **kwargs)
        

    def clean_address(self):
        address = self.cleaned_data["address"]

        location = self.geocoder.geocode(address)
        if not location:
            raise forms.ValidationError("Адрес не найден")

        self.cleaned_data["point"] = make_point_by_location(location)

        return address


class CourierForm(forms.Form):
    name = forms.CharField(label='Имя')
    use_home_location = forms.BooleanField(label='Использовать локацию дома', required=False)
    capacity = forms.IntegerField(label='Вместимость (кг)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        name = None
        if self.data:
            name = self.data.get("name")
        elif self.initial:
            name = self.initial.get("name")
        
        if not name:
            return

        courier = Courier.objects.filter(name=name).first()

        if not courier or not courier.home_location:
            self.fields["use_home_location"].disabled = True