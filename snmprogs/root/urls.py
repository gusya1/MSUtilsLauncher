"""snmprogs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.apps import apps
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='root'),
    # path('scripts/list', views.list_scripts, name='scripts/list'),
    # path('scripts/create', views.create_script, name='scripts/create'),
    # path('scripts/edit/<int:_id>/', views.edit_script),
    # path('scripts/show/<int:_id>/', views.show_script),
    # path('scripts/run/<int:_id>/', views.run_script),
    # path('demand_creator/', include('demand_creator.urls')),
    # path('processing_creator/', include('processing_creator.urls')),
    # path('accounts_syncro/', include('accounts_syncro.urls')),
]


def generate_snm_apps_paths():
    for app in apps.get_app_configs():
        if not hasattr(app, "is_snm_app"):
            continue
        if not app.is_snm_app:
            continue
        yield path('{}/'.format(app.label), include('{}.urls'.format(app.name)))


urlpatterns += list(generate_snm_apps_paths())
