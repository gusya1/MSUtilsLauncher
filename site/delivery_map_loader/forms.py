from django.forms import ClearableFileInput
import django.forms as forms


class GeoJsonFileChooseForm(forms.Form):
    date = forms.DateField(label='Выберете дату', widget=forms.DateInput(attrs={'type': 'date'}))
    file = forms.FileField(label="Выберите geoJSON файл",
                           widget=ClearableFileInput(attrs={'accept': '.geojson'}))

