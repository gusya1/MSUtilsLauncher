from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from .run.main import generate_processing
from root import forms

from .apps import ProcessingCreatorConfig as App


@permission_required('processing_creator.can_create_processing')
def index(request):
    form = forms.DateChooseForm()
    return render(request, 'base_app_page.html',
                  {
                      'title': App.verbose_name,
                      'form': form,
                      'url_target': "run"
                  })


@permission_required('processing_creator.can_create_processing')
def run(request):
    form = forms.DateChooseForm(request.GET)
    if not form.is_valid():
        return HttpResponseNotFound("Parameter \'date\' not found")
    status, output = generate_processing(form.cleaned_data['date'])
    if status:
        return render(request, 'success.html', {'changes': output[0],
                                                'change_count': len(output[0]),
                                                'errors': output[1]
                                                })
    else:
        return render(request, 'error.html', {'error': output})
