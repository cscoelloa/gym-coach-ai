import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationKind, Severity
from apps.notifications.services import notify, unread_count

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user("atleta", password="Contrasena-Larga-1")


@pytest.fixture
def otro():
    return User.objects.create_user("otro", password="Contrasena-Larga-2")


def crear(user, **kwargs):
    return Notification.objects.create(
        user=user,
        kind=kwargs.pop("kind", NotificationKind.PROGRESS_READY),
        title=kwargs.pop("title", "Aviso"),
        body=kwargs.pop("body", "Contenido"),
        **kwargs,
    )


class TestContador:
    def test_cuenta_solo_las_no_leidas(self, user):
        crear(user)
        crear(user, is_read=True)

        assert unread_count(user) == 1

class TestCreacion:
    def test_notify_crea_y_devuelve(self, user):
        notificacion = notify(
            user, kind=NotificationKind.WEIGHT_OFF_TRACK, title="Peso",
            body="Vas desviado", severity=Severity.WARNING, send_email=False,
        )

        assert notificacion.pk
        assert notificacion.severity == Severity.WARNING
        assert notificacion.badge_class == "badge-warn"
