"""
snmprogs URL Configuration.

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
from django.urls import path
from django.contrib.auth.decorators import permission_required

from . import views

app_name = 'delivery_map_creator'

app_permission = 'delivery_map_creator.can_generate_delivery_map'

urlpatterns = [
    path('', permission_required(app_permission)(views.IndexView.as_view()), name='index'),
    path('download', permission_required(app_permission)(views.download), name='download'),
]
