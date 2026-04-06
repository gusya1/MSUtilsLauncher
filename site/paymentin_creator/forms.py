import logging

from django.forms import ClearableFileInput
import django.forms as forms

from moy_sklad import getters
from moy_sklad.client import MoySkladClient
from moy_sklad.model import MoySkladCustomerOrder
from moy_sklad_settings.utils import get_moy_sklad_token
from moy_sklad.exceptions import MoySkladConnectionError

logger = logging.getLogger("paymentin_creator")

def get_order_state_choices(client: MoySkladClient):
    return list((state.name, state.name) for state in getters.get_states_for_entity(client, MoySkladCustomerOrder))

class PaymentInCreatorForm(forms.Form):
    start_date = forms.DateField(label='Начальная дата', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='Конечная дата', widget=forms.DateInput(attrs={'type': 'date'}))
    order_state = forms.CharField(label='Статус заказа')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            client = MoySkladClient(get_moy_sklad_token())
            self.fields["order_state"].widget = forms.Select(choices=get_order_state_choices(client))
            
        except MoySkladConnectionError as e:
            self.fields.clear()
            self.cleaned_data = []
            logger.warning("MoySkladConnectionError: {}".format(e))
            self.add_error(None, "Мой Склад API недоступен")
    
