import json
import logging
from urllib.parse import urlencode
import uuid
from django.shortcuts import redirect
from pydantic import ValidationError

from django.urls import reverse, reverse_lazy
from django.core.cache import cache
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from root.views import AppViewMixin

from .apps import CourierDataLoaderConfig
from .core.loader import load_courier_data
from .core.data_structure import OrdersCourierData, ResultData


class CourierDataLoaderViewMixin(AppViewMixin):
    title= CourierDataLoaderConfig.verbose_name


class PydanticValidationMixin:
    pydantic_model = None

    def get_validated_data(self, request):
        try:
            data = ""
            if request.content_type == "application/json":
                data = json.loads(request.body)
            elif "payload" in request.POST:
                data = json.loads(request.POST["payload"])
            return self.pydantic_model(**data)

        except json.JSONDecodeError:
            raise ValueError("Invalid JSON")

        except ValidationError as e:
            raise ValueError(e.errors())

    def dispatch(self, request, *args, **kwargs):
        if self.pydantic_model and request.method in ('POST', 'PUT', 'PATCH'):
            try:
                request.validated_data = self.get_validated_data(request)
            except ValueError as e:
                return JsonResponse({'errors': str(e)}, status=400)
        return super().dispatch(request, *args, **kwargs)

class ProcessView(PydanticValidationMixin, View):
    pydantic_model = OrdersCourierData

    def post(self, request, *args, **kwargs):
        key = str(uuid.uuid4())
        result: ResultData = load_courier_data(request.validated_data)
        cache.set(key, result.model_dump(), timeout=60*10)

        query_string = urlencode({"key": key})
        url = f"{reverse('courier_data_loader:result')}?{query_string}"
        return redirect(url)
    
class ResultView(CourierDataLoaderViewMixin, TemplateView):
    template_name = 'courier_data_loader/result_page.html'
    subtitle = "Результат"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        key = self.request.GET.get("key")
        if key and cache.get(key):
            context.update(cache.get(key))
        return context
    