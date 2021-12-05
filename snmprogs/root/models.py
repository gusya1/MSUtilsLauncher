from django.db import models
from django.forms import ModelForm


class Post(models.Model):
    name = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.name


class BaseScript(models.Model):
    name = models.CharField(max_length=255)
    form_obj_name = models.CharField(max_length=255)
    func_obj_name = models.CharField(max_length=255)


class BaseScriptForm(ModelForm):
    class Meta:
        model = BaseScript
        fields = ['name', 'form_obj_name', 'func_obj_name']
