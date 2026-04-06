

import logging
import uuid

from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.apps import apps
from django.urls import reverse
from django.core.cache import cache

from celery.result import AsyncResult

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

class CacheMixin:
    cache_timeout = 60 * 60 * 3 # 3 час

    cache_url_kwarg = "cache_key"

    def get_cache_key(self):
        return self.kwargs.setdefault(self.cache_url_kwarg, uuid.uuid4())

    def reverse_with_cache(self, viewname, **kwargs):
        kwargs[self.cache_url_kwarg] = self.get_cache_key()
        return reverse(viewname, kwargs=kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["cache_key"] = self.get_cache_key()

        return context

    def _get_cache_data(self):
        return cache.get(self.get_cache_key(), {})

    def _set_cache_data(self, data):
        cache.set(
            self.get_cache_key(),
            data,
            timeout=self.cache_timeout,
        )

    def _update_cache(self, key, value):
        data = self._get_cache_data()
        data[key] = value
        self._set_cache_data(data)

    def reset_cache(self):
        cache.delete(self.get_cache_key())


class ProcessView(TemplateView):
    template_name = 'process_page.html'
    processing_text = "Выполнение..."

    def get_success_url(self):
        raise NotImplementedError

    def get_task_id(self):
        raise NotImplementedError
    
    def set_result(self, result):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        task_id = self.get_task_id()
        if task_id:
            task_result = AsyncResult(task_id)
            if task_result.ready():
                result = task_result.get()
                self.set_result(result)
                return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(*args,**kwargs)
        context["processing_text"] = self.processing_text
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
