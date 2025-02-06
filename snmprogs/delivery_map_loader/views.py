import logging
from typing import Tuple

from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from .apps import DeliveryMapLoaderConfig as App
from .forms import GeoJsonFileChooseForm, PaletteForm
from .run import delivery_map_loader
from .run.projects import get_project_names
from .run.settings import DeliveryMapPaletteSettings, read_palette, write_palette


def make_project_name_choice(project_name: str) -> Tuple[str, str]:
    return project_name, project_name


def make_project_choices():
    empty_choice = ("", "")
    result = [empty_choice]
    result += list(make_project_name_choice(project_name) for project_name in get_project_names())
    return result


def filter_not_empty_value(data):
    key, value = data
    return value


def get_yandex_maps_constructor_hotbar_colors():
    return [
        "#82cdff",
        "#1e98ff",
        "#177bc9",
        "#0e4779",
        "#ffd21e",
        "#ff931e",
        "#e6761b",
        "#ed4543",
        "#56db40",
        "#1bad03",
        "#97a100",
        "#595959",
        "#b3b3b3",
        "#f371d1",
        "#b51eff",
        "#793d0e",
    ]


@permission_required('root.view_post')
def index(request):
    form = GeoJsonFileChooseForm()
    return render(request, 'base_app_page.html',
                  {
                      'title': App.verbose_name,
                      'form': form,
                      'url_target': "run",
                      'method': 'post',
                      'enctype': 'multipart/form-data',
                      'settings_url': "settings",
                      'description': 'description.html'
                  })


@permission_required('root.view_post')
def run(request):
    if request.method != 'POST':
        return
    form = GeoJsonFileChooseForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'error.html', {'error': form.errors})
    date = form.cleaned_data['date']
    file = request.FILES['file']
    geojson_data = b""
    for chunk in file.chunks():
        geojson_data += chunk
    ok, changes, errors = delivery_map_loader.run(geojson_data, date)

    if ok:
        return render(request, 'result.html', {'changes': changes, 'errors': errors})
    else:
        return render(request, 'error.html', {'errors': errors})


def get_field_label(form, field_name) -> str:
    return form[field_name].label


def get_field_value(form, field_name) -> str:
    return form.cleaned_data[field_name]


def format_field_change(form, field_name):
    return "Изменено значение поля '{}' на '{}'".format(get_field_label(form, field_name),
                                                        get_field_value(form, field_name))


def apply_settings(request):
    form = PaletteForm(get_yandex_maps_constructor_hotbar_colors(), make_project_choices(), request.POST)
    form.fill(read_palette())
    if not form.is_valid():
        return render(request, 'error.html', {'error': form.errors})

    logging.info("Changed fields: {}".format(" ,".join(form.changed_data)))
    settings_model = DeliveryMapPaletteSettings(
        delivery_order_attribute_name=get_field_value(form, 'delivery_order_attribute_name'),
        palette=dict(filter(filter_not_empty_value, form.get_color_dict())))
    write_palette(settings_model)

    changes = list(format_field_change(form, field_name) for field_name in form.changed_data)
    return render(request, 'result.html', {'changes': changes, 'errors': []})


@permission_required('root.view_post')
def settings(request):
    if request.method == 'GET':
        form = PaletteForm(get_yandex_maps_constructor_hotbar_colors(), make_project_choices())
        form.fill(read_palette())
        return render(request, 'base_app_page.html',
                      {
                          'title': "{}: Настройки".format(App.verbose_name),
                          'form': form,
                          'url_target': "settings",
                          'method': 'post',
                          'description': 'settings_description.html'
                      })
    else:
        return apply_settings(request)
