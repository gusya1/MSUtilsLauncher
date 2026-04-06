from uuid import UUID
from . import model


def get_link_to_entity_collection(entity_class):
    class_map =  {
        model.MoySkladProduct: "entity/product",
        model.MoySkladVariant: "entity/variant",
        model.MoySkladProductFolder: "entity/productfolder",
        model.MoySkladPriceType: "context/companysettings/pricetype",
        model.MoySkaldCounterparty: "entity/counterparty",
        model.MoySkladEmployee: "entity/employee",
        model.MoySkaldTask: "entity/task",
        model.MoySkladCustomerOrder: "entity/customerorder",
        model.MoySkladOrganization: "entity/organization",
        model.MoySkladProject: "entity/project",
        model.MoySkladDiscount: "entity/discount",
        model.MoySkladService: "entity/service",
        model.MoySkladBundle: "entity/bundle",
        model.MoySkladStore: "entity/store",
        model.MoySkladPaymentIn: "entity/paymentin",
    }
    for class_name, link in class_map.items():
        if issubclass(entity_class, class_name):
            return link
    raise ValueError("Unknown entity class")


def get_link_to_entity_create(entity_class):
    return {
        model.MoySkaldCounterpartyCreate: "entity/counterparty",
        model.MoySkaldTaskCreate: "entity/task",
        model.MoySkladCustomerOrderCreate: "entity/customerorder",
        model.MoySkladPaymentInCreate: "entity/paymentin",
    }[entity_class]

def get_link_to_entity_update(entity_class, id: UUID):
    return {
        model.MoySkaldCounterpartyBase: "entity/counterparty/{}",
        model.MoySkladCustomerOrderUpdate: "entity/customerorder/{}",
    }[entity_class].format(id)


def get_response_class_by_create_class(entity_class):
    return {
        model.MoySkaldCounterpartyCreate: model.MoySkaldCounterparty,
        model.MoySkaldTaskCreate: model.MoySkaldTask,
        model.MoySkladCustomerOrderCreate: model.MoySkladCustomerOrder,
        model.MoySkladPaymentInCreate: model.MoySkladPaymentIn,
    }[entity_class]

def get_response_class_by_base_class(entity_class):
    class_map = {
        model.MoySkaldCounterpartyBase: model.MoySkaldCounterparty,
        model.MoySkladCustomerOrderUpdate: model.MoySkladCustomerOrder,
        model.MoySkladPaymentInBase: model.MoySkladPaymentIn,
    }
    for class_name, response_class in class_map.items():
        if issubclass(entity_class, class_name):
            return response_class
    raise ValueError("Unknown entity base class")
