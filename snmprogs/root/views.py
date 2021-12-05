import sys

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.apps import apps
from django.contrib.auth.models import User
from django.urls import include

from .models import BaseScript, BaseScriptForm


def index(request):
    snm_apps_list = []
    for app in apps.get_app_configs():
        if not hasattr(app, "is_snm_app"):
            continue
        if not app.is_snm_app:
            continue
        snm_apps_list.append(app)
    return render(request, 'index.html', {'index_content': 'index_content.html', 'snm_apps': snm_apps_list})


def list_scripts(request):
    scripts = BaseScript.objects.all()
    return render(request, "scripts_management/list_scripts.html",
                  {
                      "scripts": scripts,
                      "form": BaseScriptForm()
                  })


def edit_script(request, _id):
    try:
        person = BaseScript.objects.get(id=_id)

        if request.method == "POST":
            form = BaseScriptForm(request.POST, instance=person)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('list')
        else:
            return render(request, "scripts_management/edit_script.html", {"form": BaseScriptForm(instance=person)})
    except BaseScript.DoesNotExist:
        return HttpResponseNotFound("<h2>Script not found</h2>")


def create_script(request):
    if request.method == "POST":
        form = BaseScriptForm(request.POST)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect('list')


def get_object_by_path(path: str):
    form_path_list = str(path).split('.')
    form = sys.modules[form_path_list[0]]
    for i in range(1, len(form_path_list)):
        form = getattr(form, form_path_list[i])
    return form


def show_script(request, _id):
    try:
        script = BaseScript.objects.get(id=_id)
        form_obj = get_object_by_path(script.form_obj_name)

        return render(request, 'utils/base_app_page.html',
                      {
                          'title': script.name,
                          'form': form_obj(),
                          'url_target': "/scripts/run/{}".format(_id)
                      })
    except BaseScript.DoesNotExist:
        return HttpResponseNotFound("<h2>Script not found</h2>")


def run_script(request, _id):
    try:
        script = BaseScript.objects.get(id=_id)

        func = get_object_by_path(script.func_obj_name)
        form_obj = get_object_by_path(script.form_obj_name)
        form = form_obj(request.GET)
        arguments = dict((key, field) for key, field in form.data.items())
        func(**arguments)
        return HttpResponse(form.fields)

    except BaseScript.DoesNotExist:
        return HttpResponseNotFound("<h2>Script not found</h2>")
