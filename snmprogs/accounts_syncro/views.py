from django.http import HttpResponse, HttpRequest, HttpResponseNotFound
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .run.main import accounts_syncro
from root import forms
from .apps import AccountsSyncConfig as App


@permission_required('root.view_post')
def index(request):
    form = forms.DateChooseForm()
    return render(request, 'base_app_page.html',
                  {
                      'title': App.verbose_name,
                      'form': form,
                      'url_target': "run"
                  })


@permission_required('root.view_post')
def run(request):
    form = forms.DateChooseForm(request.GET)
    if not form.is_valid():
        return HttpResponseNotFound()
    status, output = accounts_syncro(form.cleaned_data['date'])
    if status:
        return render(request, 'success.html', {'changes': output})
    else:
        return render(request, 'error.html', {'error': output})
    # return HttpResponse(text, content_type="text/html", status=code)
