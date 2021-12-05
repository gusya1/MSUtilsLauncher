import configparser
import os


class MOY_SKLAD:
    TOKEN = ""


class DELIVERY_MAP_GENERATOR:
    PROJECTS_BLACKLIST_ENTITY = ""
    GOOGLEMAPS_KEY = ""
    DEFAULT_COLOR = ""
    DELIVERY_TIME_MISSED_COLOR = ""


def read_config():
    config = configparser.ConfigParser()
    config.read_dict(
        {
            'moy_sklad_auch': {
                'auch_token': "",
            },
            'processing_generator': {
                'processing_plan_blacklist_entity': "",
                'store_name': ""
            },
            'delivery_map_generator': {
                'projects_blacklist_entity': "",
                'googlemaps_key': "",
                'default_color': "",
                'delivery_time_missed_color': "",
            }
        })
    settings_dir = os.path.expanduser('~')
    settings_path = os.path.join(settings_dir, "ms_settings.ini")
    if not os.path.exists(settings_path):
        os.makedirs(settings_dir, exist_ok=True)
        file = open(settings_path, 'w')
        config.write(file)

    config.read(settings_path, encoding="utf-8")
    section = config['moy_sklad_auch']
    MOY_SKLAD.TOKEN = section['auch_token']
    section = config['delivery_map_generator']
    DELIVERY_MAP_GENERATOR.PROJECTS_BLACKLIST_ENTITY = section['projects_blacklist_entity']
    DELIVERY_MAP_GENERATOR.GOOGLEMAPS_KEY = section['googlemaps_key']
    DELIVERY_MAP_GENERATOR.DEFAULT_COLOR = section['default_color']
    DELIVERY_MAP_GENERATOR.DELIVERY_TIME_MISSED_COLOR = section['delivery_time_missed_color']


read_config()

