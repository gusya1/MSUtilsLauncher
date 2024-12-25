from MSApi import MSApi, Filter, MSApiException, Expand, CustomerOrder, error_handler
from MSApi import Organization

from moy_sklad_utils import auth, custom_entity_utils, filters

from .settings import get_account_synchronize_settings

def accounts_synchronize(date):
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())

        settings = get_account_synchronize_settings()
        custom_entity = custom_entity_utils.find_custom_entity(settings.states_and_accounts_entity)
        states_and_accounts = list((entity_elem.get_name(), entity_elem.get_description())
                                   for entity_elem in custom_entity.gen_elements())

        accounts_meta_dict = {}
        for org in Organization.gen_list(filters=Filter.eq('name', settings.organization_name)):
            for account in org.gen_accounts():
                accounts_meta_dict[account.get_account_number()] = account.get_meta()
            break
        else:
            raise RuntimeError("Юрлицо \"{}\" не найдено!".format(settings.organization_name))

        if len(accounts_meta_dict) == 0:
            raise RuntimeError("Юрлицо [{}]: Счета не найдены".format(settings.organization_name))

        date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)

        change_list = []
        updatable_customerorder_list = []
        for state_name, account_name in states_and_accounts:
            account_meta = accounts_meta_dict.get(account_name)
            if account_meta is None:
                raise RuntimeError(f"Счёт \"{account_name}\" не найден")

            customer_order_filters = Filter.eq("state.name", state_name) + date_filter
            for customer_order in CustomerOrder.gen_list(expand=Expand("state"), filters=customer_order_filters):
                org_acc = customer_order.get_organization_account()
                if org_acc is not None:
                    if org_acc.get_meta() == account_meta:
                        continue

                updatable_customerorder_list.append(
                    {
                        'meta': customer_order.get_meta().get_json(),
                        'organizationAccount': {'meta': account_meta.get_json()}
                    })
                change_list.append("В заказе {} счёт изменён на {}".format(customer_order.get_name(), account_name))

        if updatable_customerorder_list:
            response = MSApi.auch_post("entity/customerorder", json=updatable_customerorder_list)
            error_handler(response)

        return True, change_list

    except MSApiException as e:
        return False, str(e)
    except RuntimeError as e:
        return False, str(e)
