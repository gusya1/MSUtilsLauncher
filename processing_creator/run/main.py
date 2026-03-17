from MSApi import MSApi, Store, Filter, MSApiException, ProcessingOrder, Expand, Processing

from moy_sklad_utils import auth, custom_entity_utils, filters

from .settings import get_processing_creator_settings


def generate_processing(date):
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())

        settings = get_processing_creator_settings()
        processing_plan_blacklist = custom_entity_utils.get_entity_element_names(
            custom_entity_utils.find_custom_entity(settings.processing_plan_blacklist_entity))

        for s in Store.gen_list(filters=Filter.eq('name', settings.store_name)):
            store = s
            break
        else:
            raise RuntimeError("Склад \'{}\' не найден!".format(settings.store_name))

        ##
        error_list = []
        change_list = []

        date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)

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
