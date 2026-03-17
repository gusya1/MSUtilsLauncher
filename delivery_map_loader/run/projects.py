from MSApi import Project, MSApi

from moy_sklad_utils import auth


def get_project_names():
    MSApi.set_access_token(auth.get_moy_sklad_token())
    return list(project.get_name() for project in Project.gen_list())