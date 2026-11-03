import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def cache_limpia():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def media_aislado(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
