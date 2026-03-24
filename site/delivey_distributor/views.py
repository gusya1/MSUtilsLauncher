import json
import logging
import re
from venv import logger

from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View
from django.http import JsonResponse
from django.forms.utils import ErrorList

from extra_views import FormSetView
from numpy import add

from moy_sklad_settings.utils import get_moy_sklad_token
from moy_sklad import getters
from moy_sklad import model
from moy_sklad.client import MoySkladClient
from moy_sklad.utils import format_moy_sklad_datetime

from yandex_geocoder.geocoder import Geocoder
from yandex_geocoder.models import Location

from .core.solution_processor import export_courier_break_points, export_route_points, export_routes_lines_to_geojson, extract_solution, make_context
from .core.delivery_data_preparator import create_data_model
from .core.solver import solve_vrp
from .core.time_intervals_identifier import parse_time_interval_safety
from .core.data_structure import CourierData, OrderData, Point
from .apps import DeliveyDistributorConfig
from .forms import CourierForm, DateChooseForm, OrderForm
from .models import Courier, DeliveryRoutingSettings

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
    
    def set_couriers(self, couriers: list[CourierData]):
        self.request.session.setdefault(self.root_key, {})["couriers"] = [courier.model_dump_json() for courier in couriers]
        self.request.session.modified = True
    
    def get_couriers(self):
        return [CourierData.model_validate_json(data) for data in self.request.session.get(self.root_key, {}).get("couriers", [])]
    
    def get_enabled_couriers(self):
        return [courier for courier in self.get_couriers() if courier.enable]
    
    def set_results(self, results: list):
        self.request.session.setdefault(self.root_key, {})["results"] = results
        self.request.session.modified = True
    
    def get_results(self):
        return self.request.session.get(self.root_key, {}).get("results", [])
    
    def reset_session(self):
        self.request.session[self.root_key] = {}
        self.request.session.modified = True

def make_point_by_location(location: Location):
    return Point(longitude=location.longitude, latitude=location.latitude)

# Create your views here.
class IndexView(AppViewMixin, DeliveryRutingSessionMixin, FormView):
    template_name = 'base_form_page.html'
    form_class = DateChooseForm
    success_url = reverse_lazy("delivey_distributor:orders")
    subtitle = "Выберите день доставки"
    
    def form_valid(self, form):
        self.reset_session()
        client = MoySkladClient(get_moy_sklad_token())
        geocoder = Geocoder()
        project_filters = ["project!={}".format(project.meta.href) for project in self.__get_projects(client, projects_blacklist)]
        date_filter = "deliveryPlannedMoment={}".format(format_moy_sklad_datetime(form.cleaned_data['date']))
        filter = ";".join(project_filters + [date_filter])
        orders = getters.walk_for_all(client, model.MoySkladCustomerOrder, filter=filter)
        order_data = [self.__get_order_data(order, geocoder) for order in orders]
        self.set_orders(order_data)
        return super().form_valid(form)
    
    def __get_order_data(self, order: model.MoySkladCustomerOrder, geocoder: Geocoder):
        delivery_time = order.find_attribute_by_name('Время доставки') # TODO mode to settings
        delivery_time = delivery_time.value if delivery_time else ""
        start_time, end_time = parse_time_interval_safety(delivery_time)
        address = order.shipmentAddress
        location = geocoder.geocode(address)
        point = make_point_by_location(location) if location else None
        return OrderData(
            name=order.name,
            point=point,
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
    template_name = 'delivey_distributor/formset_page.html'
    form_class = OrderForm
    subtitle = "Детали заказов"
    success_url = reverse_lazy("delivey_distributor:couriers")
    factory_kwargs = {'extra': 2, 'max_num': None, 'can_order': False, 'can_delete': True}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geocoder = Geocoder()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["geocoder"] = self.geocoder
        return kwargs

    def get_initial(self):
      orders = self.get_orders()
      data = [self.__get_order_form_initial_data(order) for order in orders]
      return data
    
    def formset_valid(self, formset):
        new_data = list(OrderData.model_validate(data) for data in formset.cleaned_data if data and not data.get('DELETE', False))
        self.set_orders(new_data)

        action = self.request.POST.get("action")
        if action == "save":
            return redirect(self.request.path)
        return super().formset_valid(formset)

    def __get_order_form_initial_data(self, order: OrderData):
        data = order.model_dump()
        data["has_coords"] = order.point is not None
        return data

class CourierDetailsView(AppViewMixin, DeliveryRutingSessionMixin, FormSetView):
    template_name = 'delivey_distributor/formset_page.html'
    form_class = CourierForm
    subtitle = "Детали курьеров"
    success_url = reverse_lazy("delivey_distributor:process")
    factory_kwargs = {'extra': 2, 'max_num': None, 'can_order': False, 'can_delete': True}

    def get_initial(self):
        couriers = self.get_couriers() or self.__get_couriers_by_settings()
            
        data = []
        for courier in couriers:
            data.append({
                "enable": courier.enable,
                "name": courier.name,
                "use_home_location": courier.end is not None,
                "capacity": courier.capacitiy
            })
            
        return data

    def formset_valid(self, formset):
        new_data = list(self.__get_courier_by_form_data(data, formset[i]) for i, data in enumerate(formset.cleaned_data) if data and not data.get('DELETE', False))
        
        if not any(courier.enable for courier in new_data):
            formset._non_form_errors = "Нет активных курьеров"
            return super().formset_invalid(formset)
        
        self.set_couriers(new_data)

        action = self.request.POST.get("action")
        if action == "save":
            return redirect(self.request.path)
        return super().formset_valid(formset)

    def __get_courier_by_form_data(self, data, form):
        settings: DeliveryRoutingSettings = DeliveryRoutingSettings.get_solo()
        use_home_location = data["use_home_location"]
        try:
            courier = Courier.objects.get(name=data.get("name"))
        except Courier.DoesNotExist:
            courier = None
        if use_home_location and (courier is None or courier.home_location is None):
                form.add_error("use_home_location", "Нельзя установить домашнюю локацию для этого курьера")
        return CourierData(enable=data["enable"],
                           name=data["name"], 
                           start=make_point_by_location(settings.store_location), 
                           end=make_point_by_location(courier.home_location) if use_home_location and courier else None,
                           capacitiy=data["capacity"])

    def __get_couriers_by_settings(self):
        settings = DeliveryRoutingSettings.get_solo()
        couriers_settings = settings.couriers.all()
        couriers = []
        for courier_settings in couriers_settings:
            courier_settings: Courier
            couriers.append(CourierData(name=courier_settings.name, 
                                        start=make_point_by_location(settings.store_location), 
                                        end=make_point_by_location(courier_settings.home_location),
                                        capacitiy=courier_settings.capacity))
        return couriers
    
class ProcessView(AppViewMixin, DeliveryRutingSessionMixin, TemplateView):
    template_name = 'delivey_distributor/result_page.html'
    subtitle = "Результат"

    def get(self, request, *args, **kwargs):
        orders = self.get_orders()
        # fill geocoder
        couriers = self.get_enabled_couriers()
        data = create_data_model(orders, couriers)
        solution, manager, routing = solve_vrp(data)
        if solution:
            self.set_results(extract_solution(solution, manager, routing, orders, couriers))
        else:
            print("Решение не найдено!")

        return super().get(request, *args, **kwargs)

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(*args,**kwargs)
        orders = self.get_orders()
        results = self.get_results()
        if results:
            context.update(make_context(results, orders))
        return context
    
class GetGeojsonRoutesView(DeliveryRutingSessionMixin, View):
    template_name = 'delivey_distributor/result_page.html'
    subtitle = "Результат"

    def get(self, request, *args, **kwargs):
        results = self.get_results()
        orders = self.get_orders()
        couriers = self.get_enabled_couriers()
        return JsonResponse({
            "routes": export_routes_lines_to_geojson(results, orders, couriers),
            "points": export_route_points(results, orders) + export_courier_break_points(results, couriers)
        })
