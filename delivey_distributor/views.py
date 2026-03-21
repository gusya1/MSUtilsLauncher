import logging
from os import name
from venv import logger

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from extra_views import FormSetView

from moy_sklad_settings.utils import get_moy_sklad_token
from moy_sklad import getters
from moy_sklad import model
from moy_sklad.client import MoySkladClient
from moy_sklad.utils import format_moy_sklad_datetime

from .core.time_intervals_identifier import parse_time_interval_safety
from .core.data_structures import OrderData
from .apps import DeliveyDistributorConfig
from .forms import DateChooseForm, OrderForm

logger = logging.getLogger("delivey_distributor")



class AppViewMixin:
    subtitle= ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = DeliveyDistributorConfig.verbose_name
        context['subtitle'] = self.subtitle
        return context


projects_blacklist = { # TODO move to settings
    "СВ-Ветеранов",
    "СВ-П",
    "СВ-Парнас",
    "СВ-Т"
}

class DeliveryRutingSessionMixin:
    root_key= "delivery_routing_session"

    def set_orders(self, orders: list[OrderData]):
        self.request.session.setdefault(self.root_key, {})["orders"] = [order.model_dump_json() for order in orders]
        self.request.session.modified = True

    def get_orders(self):
        return [OrderData.model_validate_json(data) for data in self.request.session.get(self.root_key, {}).get("orders", [])]


# Create your views here.
class IndexView(AppViewMixin, DeliveryRutingSessionMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = DateChooseForm
    success_url = reverse_lazy("delivey_distributor:orders")
    subtitle = "Выберите день доставки"
    
    def form_valid(self, form):
        client = MoySkladClient(get_moy_sklad_token())
        
        project_filters = ["project!={}".format(project.meta.href) for project in self.__get_projects(client, projects_blacklist)]
        date_filter = "deliveryPlannedMoment={}".format(format_moy_sklad_datetime(form.cleaned_data['date']))
        filter = ";".join(project_filters + [date_filter])
        logger.info(filter)
        orders = getters.walk_for_all(client, model.MoySkladCustomerOrder, filter=filter)
        order_data = [self.__get_order_data(order) for order in orders]
        self.set_orders(order_data)
        logger.info("Found {} orders".format(len(order_data)))
        return super().form_valid(form)
    
    def __get_order_data(self, order: model.MoySkladCustomerOrder):
        delivery_time = order.find_attribute_by_name('Время доставки') # TODO mode to settings
        delivery_time = delivery_time.value if delivery_time else ""
        start_time, end_time = parse_time_interval_safety(delivery_time)
        return OrderData(
            name=order.name,
            point=None,
            address=order.shipmentAddress,
            weight=10, # TODO add real data
            start_time=start_time,
            end_time=end_time,
        )
    
    def __get_projects(self, client, project_names):
        projects = (self.__find_project(client, name) for name in project_names)
        return [project for project in projects if project]

    def __find_project(self, client, name):
        projects = list(getters.walk_for_all(client, model.MoySkladProject, filter="name={}".format(name)))
        return projects[0] if len(projects) > 0 else None
    

class OrderDetailsView(AppViewMixin, DeliveryRutingSessionMixin, FormSetView):
    template_name = 'delivey_distributor/order_details.html'
    form_class = OrderForm
    subtitle = "Детали заказов"
    success_url = reverse_lazy("delivey_distributor:couriers")
    factory_kwargs = {'extra': 2, 'max_num': None, 'can_order': False, 'can_delete': True}

    def get_initial(self):
      orders = self.get_orders()
      data = [self.__get_order_form_initial_data(order) for order in orders]
      return data
    
    def formset_valid(self, formset):
        new_data = list(OrderData.model_validate(data) for data in formset.cleaned_data if data and not data.get('DELETE', False))
        self.set_orders(new_data)

        action = self.request.POST.get("action")
        logger.info(action)
        if action == "save":
            return redirect(self.request.path)
        return super().formset_valid(formset)

    def __get_order_form_initial_data(self, order: OrderData):
        return order.model_dump()
    
class CourierDetailsView(AppViewMixin, DeliveryRutingSessionMixin, FormSetView):
    template_name = 'delivey_distributor/order_details.html'
    form_class = OrderForm
    subtitle = "Детали курьекров"
    success_url = reverse_lazy("delivey_distributor:couriers")
    factory_kwargs = {'extra': 2, 'max_num': None, 'can_order': False, 'can_delete': True}

    