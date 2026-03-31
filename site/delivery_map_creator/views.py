from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.views.generic import FormView
from django.urls import reverse, reverse_lazy


from .AutocleanStorage import autoclean_default_storage
from .run import delivery_map_generator
from root import forms
from .apps import DeliveryMapCreatorConfig as App


class AppViewMixin:
    subtitle= ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = App.verbose_name
        context['subtitle'] = self.subtitle
        return context


class IndexView(AppViewMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = forms.DateChooseForm
    subtitle = "Выберите день доставки"
    success_url = reverse_lazy()

    def form_valid(self, form):
        errors, file_name = delivery_map_generator.run(form.cleaned_data['date'])
        return render(self.request, 'download_map.html', {'errors': errors, 'download_file': file_name})


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

