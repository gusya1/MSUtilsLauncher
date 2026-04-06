import datetime
import logging

from moy_sklad_settings.utils import get_moy_sklad_token

from .data_structure import ResultData, TaskData

from moy_sklad.utils import format_moy_sklad_datetime, make_entity_meta_filed
from moy_sklad.model import MoySkladCustomerOrder, MoySkladOperation, MoySkladPaymentIn, MoySkladPaymentInUpdate, MoySkladPaymentInCreate
from moy_sklad.client import MoySkladClient
from moy_sklad.exceptions import MoySkladError
from moy_sklad import getters, creators


logger = logging.getLogger("paymentin_creator")


def _find_paymentin_state(client: MoySkladClient, paymentin_state_name: str):
    states_list = list(state for state in getters.get_states_for_entity(client, MoySkladPaymentIn) if paymentin_state_name)
    if not states_list:
        raise ValueError("Статус входящего платежа с именем {} не найден".format(paymentin_state_name))
    return states_list[0]

def create_paymentin_for_customer_orders(data: TaskData, paymentin_state_name: str):
    client = MoySkladClient(get_moy_sklad_token())
    order_filters = [
        "moment>={}".format(format_moy_sklad_datetime(datetime.datetime.combine(data.start_date, datetime.time.min))),
        "moment<={}".format(format_moy_sklad_datetime(datetime.datetime.combine(data.end_date, datetime.time.max))),
        "state.name={}".format(data.order_state)
    ]
    created_payments = []
    try:
        state = _find_paymentin_state(client, paymentin_state_name)
        for order in getters.walk_for_all(client, MoySkladCustomerOrder, filter=";".join(order_filters)):
            logger.info("Creating payment for order {}".format(order.name))
            template: MoySkladPaymentInUpdate = getters.get_entity_template(client, MoySkladPaymentInUpdate(
                operations=[
                    MoySkladOperation(
                        meta=order.meta,
                    )
                ]
            ))
            template.state = make_entity_meta_filed(state)
            payment_in = creators.create_entity(client, MoySkladPaymentInCreate.model_validate(template.model_dump()))
            created_payments.append(payment_in.name)
    except ValueError as e:
        return ResultData(created_paymentsin=created_payments, error=str(e))
    except MoySkladError as e:
        logger.error("Error creating payment: {}".format(e))
        return ResultData(created_paymentsin=created_payments, error=str(e))

    return ResultData(created_paymentsin=created_payments)