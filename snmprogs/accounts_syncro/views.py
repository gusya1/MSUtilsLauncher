from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .run.main import accounts_syncro


@permission_required('root.view_post')
def index(request):
    return render(
        request,
        'utils/accounts_syncro.html',
    )


@permission_required('root.view_post')
def run(request):
    date = request.GET.get("date", "")
    text, code = accounts_syncro(date)
    text = "<head><meta charset=\"UTF-8\"></head><body>{}</body>".format(text)
    return HttpResponse(text, content_type="text/html", status=code)
