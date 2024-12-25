from MSApi import CompanySettings, CustomEntity


def find_custom_entity(entity_name) -> CustomEntity:
    """
    Поиск пользовательского справочника МойСклад.

    :return список элементов в справочнике
    """
    for entity in CompanySettings.gen_custom_entities():
        if entity.get_name() != entity_name:
            continue
        return entity
    else:
        raise RuntimeError("Справочник {} не найден!".format(entity_name))


def get_entity_element_names(entity: CustomEntity) -> list[str]:
    return list(entity_elem.get_name() for entity_elem in entity.gen_elements())