from django.urls import path
from django.contrib.auth.decorators import permission_required

from . import views

app_name = 'courier_data_loader'

app_permission = 'courier_data_loader.can_load_courier_data'

urlpatterns = [
    path('process', permission_required(app_permission)(views.ProcessView.as_view()), name='process'),
    path('result',  permission_required(app_permission)(views.ResultView.as_view()), name='result'),
]