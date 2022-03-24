import json

from MSApi.SalesChannel import SalesChannel
from django import forms

from MSApi import Organization, Store, CustomerOrder, Service, Search, Filter

from django.forms import Widget, MultiWidget


class DictField(Widget):
    template_name = 'dictfield.html'

    def __init__(self, widget1, attrs=None):
        self.column1_verboseName = "First column"
        self.column2_verboseName = "Second column"
        self.widget1 = widget1
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        result = super().get_context(name, value, attrs)
        result['column1_verboseName'] = self.column1_verboseName
        result['column2_verboseName'] = self.column2_verboseName
        result['widget1'] = self.widget1
        return result


# <textarea name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>
# {% if widget.value %}{{ widget.value }}{% endif %}</textarea>

def get_organization_choices():
    result = []
    for org in Organization.gen_list():
        result.append((org.get_meta().get_href(), org.get_name()))
    return result


def get_store_choices():
    result = []
    for store in Store.gen_list():
        result.append((store.get_meta().get_href(), store.get_name()))
    return result


def get_order_states_choices(search):
    result = []
    for i, state in enumerate(CustomerOrder.gen_states_list(filters=Filter.sim("name", search))):
        data = state.get_name()
        result.append(data)
    return json.dumps(result)


class OrderStatesField(forms.ChoiceField):

    @staticmethod
    def __get_order_states_choices():
        result = []
        for state in CustomerOrder.gen_states_list():
            result.append((state.get_meta().get_href(), state.get_name()))
        return result

    def __init__(self, **kwargs):
        super().__init__(choices=self.__get_order_states_choices(), **kwargs)


class OrderStringAttributesField(forms.ChoiceField):

    @staticmethod
    def __get_order_states_choices():
        result = []
        for attribute in CustomerOrder.gen_attributes_list():
            if attribute.get_type() == "string":
                result.append((attribute.get_meta().get_href(), attribute.get_name()))
        return result

    def __init__(self, **kwargs):
        super().__init__(choices=self.__get_order_states_choices(), **kwargs)


class OrderSalesChannelField(forms.ChoiceField):

    @staticmethod
    def __get_sales_channel_choices():
        result = []
        for sales_channel in SalesChannel.gen_list():
            result.append((sales_channel.get_meta().get_href(), sales_channel.get_name()))
        return result

    def __init__(self, **kwargs):
        super().__init__(choices=self.__get_sales_channel_choices(), **kwargs)


class ServiceField(forms.ChoiceField):

    @staticmethod
    def __get_services_choices():
        result = []
        for service in Service.gen_list():
            result.append((service.get_meta().get_href(), service.get_name()))
        return result

    def __init__(self, **kwargs):
        super().__init__(choices=self.__get_services_choices(), **kwargs)



class OrderSettingsForm(forms.Form):
    organization = forms.ChoiceField(label='Организация', choices=get_organization_choices())
    store = forms.ChoiceField(label='Склад', choices=get_store_choices())
    sales_channel = OrderSalesChannelField(label='Канал продаж')
    wc_id_attribute = OrderStringAttributesField(label='WcId аттрибут')


class StatusSettingsForm(forms.Form):
    pending_status = OrderStatesField(label='В ожидании оплаты', help_text="Устанавливается при создании заказа "
                                                                           "(Заказ получен, но не оплачен)")
    failed_status = OrderStatesField(label='Не удалось', help_text="Не удалось оплатить или оплата была отклонена. "
                                                                   "Нужно принимать во внимание что некоторые системы "
                                                                   "оплаты с задержкой отдают результат "
                                                                   "об статусе платежа.")
    processing_status = OrderStatesField(label='Обработка', help_text="Платеж получен — заказ ожидании исполнения")
    completed_status = OrderStatesField(label='Завершено', help_text="Заказ выполнен, не требуется никаких "
                                                                     "дополнительных действий")
    onhold__status = OrderStatesField(label='В ожидании оплаты', help_text="Требуется подтвердить оплату")
    canceled_status = OrderStatesField(label='Отменено', help_text="Отменено администратором или заказчиком — "
                                                                   "не требуется никаких дополнительных действий")
    refunded_status = OrderStatesField(label='Возвращено', help_text="Возвращается администратору — "
                                                                     "не требуется никаких дополнительных действий")


class PaymentMethodSettingsForm(forms.Form):
    payment_method_attribute = OrderStringAttributesField(label='Дополнительное поле метода оплаты')


class TableStringForm(forms.Form):

    def __init__(self, method_number: int, fields: {str: forms.Field}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method_number = method_number
        for prefix, field in fields.items():
            self.fields['{}_{}'.format(prefix, method_number)] = field

    def as_table_string(self):
        return self._html_output(
            normal_row='<td>%(errors)s%(field)s%(help_text)s</td>',
            error_row='<td colspan="2">%s</td>',
            row_ender='</td>',
            help_text_html='<br><span class="helptext">%s</span>',
            errors_on_separate_row=False,
        )


class PaymentMethodForm(TableStringForm):
    def __init__(self, method_number, initial_values=("", ""), *args, **kwargs):
        super().__init__(method_number, {
            'pm_wc': forms.CharField(label='Woocommerce', initial=initial_values[0]),
            'pm_ms': forms.CharField(label='MoySklad', initial=initial_values[1])
        }, *args, **kwargs)


class DeliveryMethodForm(TableStringForm):
    def __init__(self, method_number, initial_values=("", ""), *args, **kwargs):
        super().__init__(method_number, {
            'dm_wc': forms.CharField(label='Woocommerce метод доставки', initial=initial_values[0]),
            'ds_ms': ServiceField(label='MoySklad услуга', initial=initial_values[1])
        }, *args, **kwargs)
