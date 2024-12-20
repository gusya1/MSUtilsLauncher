import datetime

from MSApi import MSApi, MSApiException, DateTimeFilter, Expand, CustomerOrder, Demand
from MSApi import CompanySettings

from .settings import MOY_SKLAD


def generate_demands(date):
    try:
        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        for entity in CompanySettings.gen_custom_entities():
            if entity.get_name() != MOY_SKLAD.PROJECTS_BLACKLIST_ENTITY:
                continue
            project_blacklist = list(entity_elem.get_name() for entity_elem in entity.gen_elements())
            break
        else:
            raise RuntimeError("Справочник \'{}\' не найден".format(MOY_SKLAD.PROJECTS_BLACKLIST_ENTITY))

        change_list = []
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
                change_list.append("Создана отгрузка для заказа \'{}\'".format(customer_order.get_name()))
            except MSApiException as e:
                error_list.append("Ошибка создания отгрузки для заказа \"{}\": {}"
                                  .format(customer_order.get_name(), str(e)))

        return True, (change_list, error_list)

    except MSApiException as e:
        return False, str(e)
    except RuntimeError as e:
        return False, str(e)
