import configparser
import os


class MOY_SKLAD:
    TOKEN = ""
    STORE_NAME = ""
    PROJECTS_BLACKLIST_ENTITY = ""


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
            'demand_generator': {
                'projects_blacklist_entity': "",
                'store_name': ""
            },
        })
    settings_dir = os.path.expanduser('~')
    settings_path = settings_dir + "/ms_settings.ini"
    if not os.path.exists(settings_path):
        os.makedirs(settings_dir, exist_ok=True)
        file = open(settings_path, 'w')
        config.write(file)

    config.read(settings_path, encoding="utf-8")
    section = config['moy_sklad_auch']
    MOY_SKLAD.TOKEN = section['auch_token']
    section = config['demand_generator']
    MOY_SKLAD.PROJECTS_BLACKLIST_ENTITY = section['projects_blacklist_entity']
    MOY_SKLAD.STORE_NAME = section['store_name']


read_config()
