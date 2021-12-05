import datetime

from MSApi import MSApi, Store, Filter, MSApiException, DateTimeFilter, ProcessingOrder, Expand, Processing
from MSApi import CompanySettings

from .settings import MOY_SKLAD


def generate_processing(date):
    try:

        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        ##
        for entity in CompanySettings.gen_custom_entities():
            if entity.get_name() != MOY_SKLAD.PROCESSING_PLAN_BLACKLIST_ENTITY:
                continue
            processing_plan_blacklist = list(entity_elem.get_name() for entity_elem in entity.gen_elements())
            break
        else:
            raise RuntimeError("Справочник \'{}\' не найден!".format(MOY_SKLAD.PROCESSING_PLAN_BLACKLIST_ENTITY))

        for s in Store.gen_list(filters=Filter.eq('name', MOY_SKLAD.STORE_NAME)):
            store = s
            break
        else:
            raise RuntimeError("Склад \'{}\' не найден!".format(MOY_SKLAD.STORE_NAME))

        ##
        error_list = []
        change_list = []

        date_filter = DateTimeFilter.gte('deliveryPlannedMoment', date)
        date_filter += DateTimeFilter.lt('deliveryPlannedMoment', date + datetime.timedelta(days=1))

        total_count = 0
        for processing_order in ProcessingOrder.gen_list(filters=date_filter, expand=Expand("processingPlan")):
            processing_order: ProcessingOrder
            if next(processing_order.gen_processings(), None) is not None:
                continue
            processing_plan = processing_order.get_processing_plan()
            if processing_plan.get_name() in processing_plan_blacklist:
                continue
            total_count += 1
            try:
                template = Processing.get_template_by_processing_order(processing_order)
                template.get_json()["productsStore"] = {'meta': store.get_meta().get_json()}
                template.get_json()["materialsStore"] = {'meta': store.get_meta().get_json()}
                po_quantity = processing_order.get_quantity()
                template.get_json()["quantity"] *= po_quantity
                for product in template.get_json()["products"]["rows"]:
                    product["quantity"] *= po_quantity
                for material in template.get_json()["materials"]["rows"]:
                    material["quantity"] *= po_quantity

                Processing.create(template)
                change_list.append("Создана техоперация для заказа на производство\'{}\'")

            except MSApiException as e:
                error_list.append("Ошибка создания техоперации для заказа на производство\'{}\': {}"
                                  .format(processing_order.get_name(), str(e)))

        return True, (change_list, error_list)

    except MSApiException as e:
        return False, str(e)
    except RuntimeError as e:
        return False, str(e)
