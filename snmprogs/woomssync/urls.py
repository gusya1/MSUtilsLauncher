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
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('wc-change-order', views.order_changed),
    path('save-payment-methods', views.save_payment_methods, name='save-payment-methods'),
    path('delete-payment-method/<int:_id>/', views.delete_payment_method, name='delete-payment-method'),
    path('create-payment-method', views.create_payment_method, name='create-payment-method'),
    path('ajax/autocomplete-select/<str:entity_name>/', views.ajax_autocomplete_select,
         name='ajax-autocomplete-select'),
]
