from django.shortcuts import render

from django.views.generic import FormView

from .apps import DeliveyDistributorConfig
from .forms import DateChooseForm

# Create your views here.
class IndexView(FormView):
    template_name = 'base_form_page.html'
    form_class = DateChooseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = DeliveyDistributorConfig.verbose_name
        return context