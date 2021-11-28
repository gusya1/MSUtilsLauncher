import datetime

from MSApi import MSApi, Store, Filter, MSApiException, DateTimeFilter, ProcessingOrder, Expand, Processing, \
    CustomerOrder, error_handler
from MSApi import CompanySettings, Organization

from .settings import MOY_SKLAD


def accounts_syncro(date_string: str):
    try:
        if not date_string:
            raise RuntimeError("Please, choose the date!")
        try:
            date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError as e:
            raise RuntimeError("Incorrect date!")

        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        ##
        for entity in CompanySettings.gen_custom_entities():
            if entity.get_name() != MOY_SKLAD.STATES_AND_ACCOUNTS_ENTITY:
                continue
            states_and_accounts = list((entity_elem.get_name(), entity_elem.get_description())
                                             for entity_elem in entity.gen_elements())
            break
        else:
            raise RuntimeError("Entity {} not found!".format(MOY_SKLAD.STATES_AND_ACCOUNTS_ENTITY))

        accounts_meta_dict = {}
        for org in Organization.gen_list(filters=Filter.eq('name', MOY_SKLAD.ORGANIZATION_NAME)):
            for account in org.gen_accounts():
                accounts_meta_dict[account.get_account_number()] = account.get_meta()
            break
        else:
            raise RuntimeError("Organization {} not found!".format(MOY_SKLAD.ORGANIZATION_NAME))

        if len(accounts_meta_dict) == 0:
            raise RuntimeError("Accounts list is empty!")

        date_filter = DateTimeFilter.gte('deliveryPlannedMoment', date)
        date_filter += DateTimeFilter.lt('deliveryPlannedMoment', date + datetime.timedelta(days=1))

        updatable_customerorder_list = []
        for state_name, account_name in states_and_accounts:
            account_meta = accounts_meta_dict.get(account_name)
            if account_meta is None:
                raise RuntimeError(f"Account name \"{account_name}\" not found")

            filters = Filter.eq("state.name", state_name) + date_filter
            for customer_order in CustomerOrder.gen_list(expand=Expand("state"), filters=filters):
                org_acc = customer_order.get_organization_account()
                if org_acc is not None:
                    if org_acc.get_meta() == account_meta:
                        continue

                updatable_customerorder_list.append(
                    {
                        'meta': customer_order.get_meta().get_json(),
                        'organizationAccount': {'meta': account_meta.get_json()}
                    })

        if updatable_customerorder_list:
            response = MSApi.auch_post("entity/customerorder", json=updatable_customerorder_list)
            error_handler(response)

        result_text = "<h2>Accounts changed: {}</h2>".format(len(updatable_customerorder_list))
        return result_text, 200

    except MSApiException as e:
        return "MSApi error: {}".format(str(e)), 400
    except RuntimeError as e:
        return "Runtime error: {}".format(str(e)), 400
