import configparser
import os


class MOY_SKLAD:
    TOKEN = ""
    STATES_AND_ACCOUNTS_ENTITY = ""
    ORGANIZATION_NAME = ""


def read_config():
    config = configparser.ConfigParser()
    config.read_dict(
        {
            'moy_sklad_auch': {
                'auch_token': "",
            },
            'accounts_syncro': {
                'states_and_accounts_entity': "",
                'organization_name': ""
            }
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
    section = config['accounts_syncro']
    MOY_SKLAD.STATES_AND_ACCOUNTS_ENTITY = section['states_and_accounts_entity']
    MOY_SKLAD.ORGANIZATION_NAME = section['organization_name']


read_config()
