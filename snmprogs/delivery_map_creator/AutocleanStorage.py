from django.conf import settings
from django.core.files.storage import FileSystemStorage
import threading
from django.conf import settings


class AutocleanStorage(FileSystemStorage):
    def __init__(self, file_lifetime=60, **kwargs):
        super().__init__(**kwargs)
        self.file_lifetime = file_lifetime

    def _save(self, name, content):
        true_filename = super()._save(name, content)
        t = threading.Timer(self.file_lifetime, self.delete, args=[true_filename])
        t.start()
        return true_filename


autoclean_default_storage = AutocleanStorage(location=settings.TEMP_ROOT, base_url=settings.TEMP_URL)
