import os

from django.http import HttpResponse, HttpRequest, HttpResponseNotFound
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.formats import date_format

from .run import delivery_map_loader
from .forms import GeoJsonFileChooseForm, SettingsForm
from .apps import DeliveryMapLoaderConfig as App
from .run.palette import change_palette


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
    file = request.FILES['file']
    geojson_data = b""
    for chunk in file.chunks():
        geojson_data += chunk
    ok, changes, errors = delivery_map_loader.run(geojson_data)

    if ok:
        return render(request, 'result.html', {'changes': changes, 'errors': errors})
    else:
        return render(request, 'error.html', {'errors': errors})


@permission_required('root.view_post')
def settings(request):
    if request.method == 'GET':
        form = SettingsForm()
        return render(request, 'base_app_page.html',
                      {
                          'title': "{}: Настройки".format(App.verbose_name),
                          'form': form,
                          'url_target': "settings",
                          'method': 'post',
                          'description': 'settings_description.html'
                      })
    else:
        form = SettingsForm(request.POST)
        if form.is_valid():
            project_by_color = {}
            for key, data in form.data.items():
                if key in form.fields.keys() and len(data) != 0:
                    project_by_color[key] = data
            ok, changes, errors = change_palette(project_by_color)
            return render(request, 'result.html', {'changes': changes, 'errors': errors})
        else:
            return render(request, 'error.html', {'error': form.errors})
