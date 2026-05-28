import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")


def pytest_configure(config):
    os.environ["DATABASE_URL"] = "postgresql://esgsync:esgsync@localhost:5432/esgsync_test"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
    os.environ["DEBUG"] = "True"
