from django.http import HttpResponse, HttpRequest, HttpResponseNotFound, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

import re

ORGANIZATION_NAME = ""
STORE_NAME = "Основной склад"

STATES_DICT = {
    "Новый": 'cod',
    "оплачен на сайте": 'tinkoff'
}

PROJECTS_DICT = {
    'С-Т': 'Пункт №1 ТУХАЧЕВСКОГО',
    'С-П': 'Пункт №2 ПУШКИН'
}

DELIVERY_DICT = {
    "Зона №6 (красная зона)": "37d8cd7f-238c-11eb-0a80-046a0001273e",
    "Зона №1 (зелёная зона)": "e4ca996c-238a-11eb-0a80-063300016fe1",
    "Зона №2 (оранжевая зона)": "e4ca996c-238a-11eb-0a80-063300016fe1",
    "Зона №3 (синяя зона)": "a91db949-5572-11eb-0a80-003a0005e730",
    "Зона №4 (фиолетовая зона)": "71dbb4a1-9f5c-11ea-0a80-0404000afc45"
}

from .forms import OrderSettingsForm, OrderStatesField, StatusSettingsForm, \
    PaymentMethodSettingsForm, PaymentMethodForm, DeliveryMethodForm, get_order_states_choices


class MultiValuesSettings:

    def __init__(self, **kwargs):
        self.title = kwargs.get('title') or ""
        self.root_form = kwargs.get('root_form')
        self.root_save_url = kwargs.get('root_save_url')
        self.sub_field_change_title = kwargs.get('sub_field_change_title') or ""
        self.sub_field_form = kwargs.get('sub_field_form') or ""
        self.sub_field_form_list = kwargs.get('sub_field_form_list') or ""
        self.sub_field_delete_url = kwargs.get('sub_field_delete_url') or ""
        self.sub_field_save_edit_url = kwargs.get('sub_field_save_edit_url') or ""
        self.sub_field_create_title = kwargs.get('sub_field_create_title') or ""
        self.sub_field_save_create_url = kwargs.get('sub_field_save_create_url') or ""


@permission_required('root.view_post')
def index(request):
    my_choice = OrderStatesField()
    # field_name = 'my_choice'
    # field_value = 1

    my_choice_html = my_choice.widget.render("name", 1)
    # return render(request, 'template.html', {'my_choice': my_choice_html})
    payment_forms = []
    for i, (ms, wc) in enumerate(STATES_DICT.items()):
        form = PaymentMethodForm(i, (wc, ms))
        payment_forms.append(form)

    payment_method_settings_config = MultiValuesSettings(
        title="Настройки методов оплаты",
        root_form=PaymentMethodSettingsForm(),
        root_save_url="save-payment-methods",  #TODO change
        sub_field_change_title="Изменить методы оплаты",
        sub_field_form=PaymentMethodForm(0),
        sub_field_form_list=payment_forms,
        sub_field_delete_url="delete-payment-method",
        sub_field_save_edit_url="save-payment-methods",
        sub_field_create_title="Добавить новый метод оплаты",
        sub_field_save_create_url="create-payment-method",
    )

    delivery_forms = []
    for i, (wc, ms) in enumerate(DELIVERY_DICT.items()):
        form = DeliveryMethodForm(i, (wc, ms))
        delivery_forms.append(form)

    delivery_methods_settings_config = MultiValuesSettings(
        title="Настройки зон доставки",
        root_form=None,
        root_save_url="save-payment-methods",  # TODO change
        sub_field_change_title="Изменить зоны доставки",
        sub_field_form=DeliveryMethodForm(0),
        sub_field_form_list=delivery_forms,
        sub_field_delete_url="delete-payment-method",
        sub_field_save_edit_url="save-payment-methods",
        sub_field_create_title="Добавить новую зону доставки",
        sub_field_save_create_url="create-payment-method",
    )

    return render(request, 'settings.html', {
        'form': OrderSettingsForm(),
        'status_form': StatusSettingsForm(),
        'payment_method_settings_config': payment_method_settings_config,
        'delivery_methods_settings_config': delivery_methods_settings_config,
        })


@permission_required('root.view_post')
def ajax_autocomplete_select(request, entity_name):
    query = request.GET.get('q') or ""
    if entity_name == "order_state":
        data = get_order_states_choices(query)
    else:
        return HttpResponseNotFound("Entity \'{}\' not found".format(entity_name))
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


@permission_required('root.view_post')
def save_payment_methods(request):
    return HttpResponseRedirect("./")


@permission_required('root.view_post')
def delete_payment_method(request, _id):
    return HttpResponseNotFound()


@permission_required('root.view_post')
def create_payment_method(request):
    return HttpResponseNotFound()

def order_changed(request):
    return HttpResponse("text", content_type="text/html", status=200)


def order_created(request):
    return HttpResponse("text", content_type="text/html", status=200)
