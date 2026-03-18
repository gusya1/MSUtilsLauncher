from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from .AutocleanStorage import autoclean_default_storage
from .run import delivery_map_generator
from root import forms
from .apps import DeliveryMapCreatorConfig as App


@permission_required('delivery_map_creator.can_generate_delivery_map')
def index(request):
    form = forms.DateChooseForm()
    return render(request, 'base_app_page.html',
                  {
                      'title': App.verbose_name,
                      'form': form,
                      'url_target': "run"
                  })


@permission_required('delivery_map_creator.can_generate_delivery_map')
def run(request):
    form = forms.DateChooseForm(request.GET)
    if not form.is_valid():
        return HttpResponseNotFound()
    errors, file_name = delivery_map_generator.run(form.cleaned_data['date'])
    return render(request, 'download_map.html', {'errors': errors, 'download_file': file_name})


@permission_required('delivery_map_creator.can_generate_delivery_map')
def download(request):
    download_file = request.GET.get("file_name")
    if not download_file:
        return HttpResponseNotFound()
    try:
        file = autoclean_default_storage.open(download_file)
        response = HttpResponse(file.read(), content_type="application/geojson")
        response['Content-Disposition'] = 'inline; filename=' + download_file
        return response
    except OSError:
        return HttpResponseNotFound()

