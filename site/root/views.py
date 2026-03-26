

import logging

from django.shortcuts import render
from django.apps import apps

from .apps import SnmAppBase

logger = logging.getLogger("django")

class AppViewMixin:
    subtitle= ""
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['subtitle'] = self.subtitle
        return context


def index(request):
    snm_apps_list = []
    for app in apps.get_app_configs():
        logger.info(app)
        if not issubclass(type(app), SnmAppBase):
            continue
        if not app.display_in_menu:
            continue
        snm_apps_list.append(app)
    return render(request, 'index.html', {'index_content': 'index_content.html', 'snm_apps': snm_apps_list})
