from MSApi import MSApi, MSApiException, Expand, CustomerOrder, Demand

from moy_sklad_utils import auth, custom_entity_utils, filters

from .settings import get_demand_creator_settings


def generate_demands(date):
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())

        settings = get_demand_creator_settings()
        project_blacklist = custom_entity_utils.get_entity_element_names(
            custom_entity_utils.find_custom_entity(settings.projects_blacklist_entity))

        change_list = []
        error_list = []

        date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)

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
