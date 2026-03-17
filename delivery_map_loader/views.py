import logging
from typing import Tuple

from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from .apps import DeliveryMapLoaderConfig as App
from .forms import GeoJsonFileChooseForm
from .run import delivery_map_loader
from .run.projects import get_project_names


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
