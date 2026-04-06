from django.urls import path
from django.contrib.auth.decorators import permission_required

from . import views

app_name = 'paymentin_creator'

app_permission = 'paymentin_creator.can_create_paymentin'

urlpatterns = [
    path('', permission_required(app_permission)(views.IndexView.as_view()), name='index'),
    path('<uuid:cache_key>/process', permission_required(app_permission)(views.ProcessView.as_view()), name='process'),
    path('<uuid:cache_key>/result', permission_required(app_permission)(views.ResultView.as_view()), name='result'),
]
