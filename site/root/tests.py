from django.test import TestCase
from django.db import IntegrityError, models, transaction

from .models import SingletonModelMixin
from django.test import TestCase
from django.db import connection
from django.db import models


class TestSingletonModel(SingletonModelMixin):
    value = models.IntegerField(default=0)

    class Meta:
        app_label = "tests_tmp"


class SingletonTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(TestSingletonModel)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestSingletonModel)
        super().tearDownClass()

    def test_create_singleton(self):
        obj = TestSingletonModel.get_solo()

        self.assertEqual(obj.pk, 1)
        self.assertEqual(TestSingletonModel.objects.count(), 1)

    def test_second_create_updates_same_row(self):
        obj1 = TestSingletonModel.get_solo()
        obj1.value = 10
        obj1.save()

        obj2 = TestSingletonModel()
        obj2.value = 20
        obj2.save()

        self.assertEqual(TestSingletonModel.objects.count(), 1)
        self.assertEqual(TestSingletonModel.get_solo().value, 20)

    def test_multiple_get_solo_returns_same_instance(self):
        obj1 = TestSingletonModel.get_solo()
        obj2 = TestSingletonModel.get_solo()

        self.assertEqual(obj1.pk, obj2.pk)

    def test_manual_create_does_not_duplicate(self):
        TestSingletonModel.objects.create()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TestSingletonModel.objects.create()

        self.assertEqual(TestSingletonModel.objects.count(), 1)