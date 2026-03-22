from django.db import models

class SingletonModelMixin(models.Model):
    """
    Миксин для модели Django, обеспечивающий существование только одной записи.
    При создании нового объекта вместо добавления записи обновляется существующая.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Если у объекта нет первичного ключа (т.е. это новый объект)
        if not self.pk:
            # Получаем класс модели (текущий)
            model_class = self.__class__
            # Пытаемся найти существующую запись
            existing = model_class.objects.first()
            if existing is not None:
                # Присваиваем текущему объекту pk существующей записи
                # Это заставит Django выполнить UPDATE, а не INSERT
                self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj