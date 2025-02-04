from snmprogs import settings

import pydantic as pdt

from typing import Type

import os
import json

def get_settings_file_path():
  return os.path.join(settings.STATIC_ROOT, "settings.json")

def read_settings():
  settings_file_path = get_settings_file_path()
  settings_file = open(settings_file_path, encoding="utf-8")
  return json.load(settings_file)

def write_settings(settings):
  settings_file_path = get_settings_file_path()
  settings_file = open(settings_file_path, "w", encoding="utf-8")
  json.dump(settings, settings_file, ensure_ascii=False, indent=4)

def get_settings(group: str, model_type: Type[pdt.BaseModel]) -> pdt.BaseModel:
  json_data = read_settings()
  return model_type.model_validate(json_data[group])

def write_settings_group(group: str, model: pdt.BaseModel):
  json_data = read_settings()
  json_data[group] = model.model_dump()
  write_settings(json_data)