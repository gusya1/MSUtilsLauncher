import uuid

from django.shortcuts import render
from django.views.generic import FormView, TemplateView, View


from root.views import CacheMixin, ProcessView

from .core.data_structure import ResultData, TaskData

from .tasks import accounts_synchronize_task
from root import forms
from .apps import AccountsSyncConfig as App


class AppViewMixin:
    subtitle= ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = App.verbose_name
        context['subtitle'] = self.subtitle
        return context

class AccountsSyncronizeCacheMixin(CacheMixin):
    def set_task_id(self, task_id: uuid.UUID):
        self._update_cache("task_id", task_id)

    def get_task_id(self) -> uuid.UUID:
        return self._get_cache_data().get("task_id", None)
    
    def set_result(self, results: ResultData):
        self._update_cache("results", results.model_dump_json())

    def get_result(self):
        results = self._get_cache_data().get("results", None)
        if results:
            return ResultData.model_validate_json(results)
        return None


class IndexView(AppViewMixin, AccountsSyncronizeCacheMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = forms.DateChooseForm
    subtitle = "Выберите день для синхронизации"

    def get_success_url(self):
        return self.reverse_with_cache("accounts_synchronize:process")

    def form_valid(self, form):
        data  = TaskData.model_validate(form.cleaned_data)
        task = accounts_synchronize_task.delay(data.model_dump_json())
        self.set_task_id(task.id)
        return super().form_valid(form)
        

class AccountsSyncronizeProcessView(AppViewMixin, AccountsSyncronizeCacheMixin, ProcessView):
    subtitle = "Выполнение"
    processing_text = "Синхронизация расчетных счетов..."

    def get_success_url(self):
        return self.reverse_with_cache("accounts_synchronize:result")

    def set_result(self, result):
        super().set_result(ResultData.model_validate_json(result))


class ResultView(AppViewMixin, AccountsSyncronizeCacheMixin, View):
    subtitle = "Результат"

    def get(self, request, *args, **kwargs):
        result = self.get_result()
        if not result.error:
            return render(request, 'success.html', {'changes': result.change_list})
        else:
            return render(request, 'error.html', {'error': result.error})