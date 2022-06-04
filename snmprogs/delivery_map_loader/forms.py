from MSApi import Project
from django.forms import forms, ChoiceField, Select, ClearableFileInput
from django.core.validators import FileExtensionValidator

from .run.palette import get_projects_by_color, delete_palette


class GeoJsonFileChooseForm(forms.Form):
    file = forms.FileField(label="Выберите geoJSON файл",
                           widget=ClearableFileInput(attrs={'accept': '.geojson'}))


class ColoredChoiceField(ChoiceField):
    def __init__(self, *, color, **kwargs):
        super().__init__(widget=Select(
            attrs={'style': 'background-color: {};'.format(color)}), **kwargs)


class SettingsForm(forms.Form):

    _color_list = [
        "#82cdff",
        "#1f98ff",
        "#187bc9",
        "#0f4879",
        "#ffd21e",
        "#ff931f",
        "#e6761c",
        "#ed4644",
        "#57db41",
        "#1bad03",
        "#97a101",
        "#5a5a5a",
        "#b3b3b3",
        "#f371d1",
        "#b51eff",
        "#793d0e",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        projects_tuple = (("", ""),) + self._get_projects_tuple()

        projects_by_color = {}
        try:
            projects_by_color = get_projects_by_color()
        except FileNotFoundError:
            pass
        except RuntimeError:
            delete_palette()

        for color in self._color_list:
            current_project = projects_by_color.get(color, None)
            if current_project is not None:
                current_project = current_project.get_name()
            self.fields[color] = ColoredChoiceField(color=color,
                                                    choices=projects_tuple,
                                                    required=False,
                                                    initial=current_project)

    def _get_projects_tuple(self):
        return tuple((proj.get_name(), proj.get_name()) for proj in Project.gen_list())
