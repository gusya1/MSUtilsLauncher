from django.urls import path

from . import views

app_name = 'courier_data_loader'

urlpatterns = [
    path('process', views.ProcessView.as_view(), name='process'),
    path('result', views.ResultView.as_view(), name='result'),
]