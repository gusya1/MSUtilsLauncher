from django.urls import path
from django.contrib.auth.decorators import permission_required

from . import views

app_name = 'delivery_distributor'

app_permission = 'delivery_distributor.can_make_delivery_routing'

urlpatterns = [
    path('', permission_required(app_permission)(views.IndexView.as_view()), name='index'),
    path('orders/<uuid:cache_key>/', permission_required(app_permission)(views.OrderDetailsView.as_view()), name='orders'),
    path('couriers/<uuid:cache_key>/', permission_required(app_permission)(views.CourierDetailsView.as_view()), name='couriers'),
    path('routing-details/<uuid:cache_key>/', permission_required(app_permission)(views.RoutingDetailsView.as_view()), name='routing_details'),
    path('process/<uuid:cache_key>/', permission_required(app_permission)(views.ProcessView.as_view()), name='process'),
    path('results/<uuid:cache_key>/', permission_required(app_permission)(views.ResultsView.as_view()), name='results'),
    path('get-routes/<uuid:cache_key>/', permission_required(app_permission)(views.GetGeojsonRoutesView.as_view()), name='get_routes'),
]
