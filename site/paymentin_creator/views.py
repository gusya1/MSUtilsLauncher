import datetime
import uuid

from django.views.generic import FormView, TemplateView
from django.urls import reverse
from django.shortcuts import redirect
from django.core.cache import cache

from celery.result import AsyncResult

from root.views import CacheMixin, ProcessView

from .core.data_structure import ResultData, TaskData

from .tasks import create_paymentin_task
from .models import PaymentInCreatorSettings
from .forms import PaymentInCreatorForm
from .apps import PaymentinCreatorConfig as App


class AppViewMixin:
    subtitle= ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = App.verbose_name
        context['subtitle'] = self.subtitle
        return context


class PaymentCreatorCacheMixin(CacheMixin):
    def set_task_id(self, task_id: uuid):
        self._update_cache("task_id", task_id)

    def get_task_id(self) -> uuid:
        return self._get_cache_data().get("task_id", None)
    
    def set_result(self, results: ResultData):
        self._update_cache("results", results.model_dump_json())

    def get_result(self):
        results = self._get_cache_data().get("results", None)
        if results:
            return ResultData.model_validate_json(results)
        return None


class IndexView(AppViewMixin, PaymentCreatorCacheMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = PaymentInCreatorForm

    def get_success_url(self):
        return self.reverse_with_cache("paymentin_creator:process")

    def form_valid(self, form):
        data  = TaskData.model_validate(form.cleaned_data)
        task = create_paymentin_task.delay(data.model_dump_json())
        self.set_task_id(task.id)
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['start_date'] = datetime.date.today().isoformat()
        initial['end_date'] = datetime.date.today().isoformat()
        initial['order_state'] = PaymentInCreatorSettings.get_solo().order_state
        return initial
    

class PaymentInCreatorProcessView(AppViewMixin, PaymentCreatorCacheMixin, ProcessView):
    subtitle = "Выполнение"
    processing_text = "Создание входящих платежей..."

    def get_success_url(self):
        return self.reverse_with_cache("paymentin_creator:result")

    def set_result(self, result):
        super().set_result(ResultData.model_validate_json(result))


class ResultView(AppViewMixin, PaymentCreatorCacheMixin, TemplateView):
    template_name = 'paymentin_creator/result_page.html'
    subtitle = "Результат"

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(*args,**kwargs)
        result = self.get_result()
        if result:
            context.update(result.model_dump())
        return context