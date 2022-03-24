import sys

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.apps import apps
from django.contrib.auth.models import User
from django.urls import include

from .apps import SnmAppBase


def index(request):
    snm_apps_list = []
    for app in apps.get_app_configs():
        print(app)
        if not issubclass(type(app), SnmAppBase):
            continue
        if not app.display_in_menu:
            continue
        snm_apps_list.append(app)
    return render(request, 'index.html', {'index_content': 'index_content.html', 'snm_apps': snm_apps_list})
