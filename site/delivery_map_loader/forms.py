from django.forms import ChoiceField, Select, ClearableFileInput
import django.forms as forms


class GeoJsonFileChooseForm(forms.Form):
    date = forms.DateField(label='Выберете дату', widget=forms.DateInput(attrs={'type': 'date'}))
    file = forms.FileField(label="Выберите geoJSON файл",
                           widget=ClearableFileInput(attrs={'accept': '.geojson'}))


class ColoredChoiceField(ChoiceField):
    def __init__(self, *, color, **kwargs):
        super().__init__(widget=Select(
            attrs={'style': 'background-color: {};'.format(color)}), **kwargs)