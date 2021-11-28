import datetime

from MSApi import MSApi, Store, Filter, MSApiException, DateTimeFilter, ProcessingOrder, Expand, Processing, \
    CustomerOrder, Demand
from MSApi import CompanySettings

from .settings import *


def generate_demands(date_string: str):
    try:
        if not date_string:
            raise RuntimeError("Please, choose the date!")
        try:
            date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError as e:
            raise RuntimeError("Incorrect date!")

        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        for entity in CompanySettings.gen_custom_entities():
            if entity.get_name() != MOY_SKLAD.PROJECTS_BLACKLIST_ENTITY:
                continue
            project_blacklist = list(entity_elem.get_name() for entity_elem in entity.gen_elements())
            break
        else:
            raise RuntimeError("Entity {} not found!".format(MOY_SKLAD.PROJECTS_BLACKLIST_ENTITY))

        error_list = []

        date_filter = DateTimeFilter.gte('deliveryPlannedMoment', date)
        date_filter += DateTimeFilter.lt('deliveryPlannedMoment', date + datetime.timedelta(days=1))

        total_count = 0
        for customer_order in CustomerOrder.gen_list(filters=date_filter, expand=Expand("project")):
            customer_order: CustomerOrder
            if next(customer_order.gen_demands(), None) is not None:
                continue
            project = customer_order.get_project()
            if project is not None:
                if project.get_name() in project_blacklist:
                    continue
            total_count += 1
            try:
                Demand.get_demand_template_by_customer_order(customer_order).create_new()
            except MSApiException as e:
                error_list.append("Demand for {} customer order create failed: {}" .format(customer_order.get_name(), str(e)))

        result_text = "<h2>Demands created: {}/{}</h2>".format(total_count - len(error_list), total_count)
        if len(error_list) != 0:
            result_text += "<p>Errors:</p>"
            for i, error in enumerate(error_list):
                result_text += f"<li><b>[{i}]</b> {error}</li>"
        return result_text, 200

    except MSApiException as e:
        return "MSApi error: {}".format(str(e)), 400
    except RuntimeError as e:
        return "Runtime error: {}".format(str(e)), 400
