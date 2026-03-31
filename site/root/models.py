from django.db import models

class SingletonModelMixin(models.Model):
    singleton_pk = 1

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self.singleton_pk
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=cls.singleton_pk)
        return obj
    
    def __str__(self):
        return self._meta.verbose_name.capitalize()