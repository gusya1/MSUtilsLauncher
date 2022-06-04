import os
import re

import pandas as pd
from MSApi import Project
from snmprogs import settings
from delivery_map_loader.apps import DeliveryMapLoaderConfig as App


def get_palette_path():
    path = os.path.join(settings.MEDIA_ROOT, "apps",  App.name, "settings")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "palette.csv")


def delete_palette():
    os.remove(get_palette_path())


def change_palette(project_by_color):
    try:
        df = pd.DataFrame(project_by_color.items(), columns=['Color', 'Project'])
        df.to_csv(get_palette_path(), index=False)
        get_projects_by_color()
        return True, ["Палитра изменена"], []
    except IOError as e:
        return False, [], [str(e)]
    except RuntimeError as e:
        return False, [], [str(e)]


def get_projects_by_color():
    projects = list(Project.gen_list())

    result = {}

    df = pd.read_csv(get_palette_path())
    try:

        for i, color, name in df.itertuples(index=True, name=None):
            if name != name:
                continue
            if not re.match(r"#[abcdef1234567890]{6}", color):
                raise RuntimeError("Строка {}: Неправильный формат цвета".format(i))
            for project in projects:
                if project.get_name() != name:
                    continue
                result[color] = project
                break
            else:
                raise RuntimeError("Строка {}: Проект {} не найден".format(i, name))

    except ValueError as e:
        raise RuntimeError("Неправильный формат файла")
    return result
