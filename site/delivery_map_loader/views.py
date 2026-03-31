import logging
from typing import Tuple

from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.views.generic import FormView

from .apps import DeliveryMapLoaderConfig as App
from .forms import GeoJsonFileChooseForm
from .run import delivery_map_loader
from .run.projects import get_project_names

class AppViewMixin:
    subtitle= ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = App.verbose_name
        context['subtitle'] = self.subtitle
        return context

class IndexView(AppViewMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = GeoJsonFileChooseForm
    subtitle = "Выберите день доставки"

    def form_valid(self, form):
        date = form.cleaned_data['date']
        file = self.request.FILES['file']
        geojson_data = b""
        for chunk in file.chunks():
            geojson_data += chunk
        ok, changes, errors = delivery_map_loader.run(geojson_data, date)

        if ok:
            return render(self.request, 'result.html', {'changes': changes, 'errors': errors})
        else:
            return render(self.request, 'error.html', {'errors': errors})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_enctype"] = "multipart/form-data"
        return context