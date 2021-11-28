
from django.http import HttpResponse
from django.shortcuts import render
from django.apps import apps
from django.contrib.auth.models import User


def index(request):
    return render(
        request,
        'index.html',
    )
