from django.forms import ChoiceField, Select, ClearableFileInput
import django.forms as forms

from typing import List, Tuple

from .run.settings import DeliveryMapPaletteSettings


class GeoJsonFileChooseForm(forms.Form):
    date = forms.DateField(label='Выберете дату', widget=forms.DateInput(attrs={'type': 'date'}))
    file = forms.FileField(label="Выберите geoJSON файл",
                           widget=ClearableFileInput(attrs={'accept': '.geojson'}))


class ColoredChoiceField(ChoiceField):
    def __init__(self, *, color, **kwargs):
        super().__init__(widget=Select(
            attrs={'style': 'background-color: {};'.format(color)}), **kwargs)


class PaletteForm(forms.Form):
    delivery_order_attribute_name = forms.CharField(label='Имя аттрибута очерёдности доставки')

    def __init__(self, colors: List[str], choices: List[Tuple[str, str]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors = colors
        for color in self.colors:
            self.fields[color] = ColoredChoiceField(color=color,
                                                    choices=choices,
                                                    required=False)

    def fill(self, model: DeliveryMapPaletteSettings):
        for color in self.colors:
            current_project = model.palette.get(color, None)
            colored_field: ColoredChoiceField = self.fields[color]
            colored_field.initial = current_project

        delivery_order_attribute_name_field: forms.CharField = self.fields['delivery_order_attribute_name']
        delivery_order_attribute_name_field.initial = model.delivery_order_attribute_name



    def get_color_dict(self):
         return list((key, data) for key, data in self.data.items() if key in self.colors)
