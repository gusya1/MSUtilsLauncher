import pydantic as pdt

from settings_manager import settings_manager

class AccountSynchronizeSettings(pdt.BaseModel):
    states_and_accounts_entity: str
    organization_name: str


def get_account_synchronize_settings() -> AccountSynchronizeSettings:
    return settings_manager.get_settings("accounts_synchronize", AccountSynchronizeSettings)