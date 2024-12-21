from snmprogs import settings

import pydantic as pdt

import os
import json


def get_settings(group: str, model_type: type[pdt.BaseModel]) -> pdt.BaseModel:
  settings_file_path = os.path.join(settings.STATIC_ROOT, "settings.json")
  settings_file = open(settings_file_path, encoding="utf-8")
  json_data = json.load(settings_file)
  return model_type.model_validate(json_data[group])