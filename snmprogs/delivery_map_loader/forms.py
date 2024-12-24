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


class PaletteForm(forms.Form):

    def __init__(self, colors: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors = colors

    def fill(self, choices: list[tuple[str, str]], projects_by_color: dict[str, str]):
        for color in self.colors:
            current_project = projects_by_color.get(color, None)
            self.fields[color] = ColoredChoiceField(color=color,
                                                    choices=choices,
                                                    required=False,
                                                    initial=current_project)

    def get_color_dict(self):
         return list((key, data) for key, data in self.data.items() if key in self.colors)
