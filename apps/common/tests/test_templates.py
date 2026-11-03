from pathlib import Path

import pytest
from django.conf import settings
from django.template import engines
from django.urls import reverse

PLANTILLAS = sorted(Path(settings.BASE_DIR, "templates").rglob("*.html"))


def test_queda_la_cascara():
    assert len(PLANTILLAS) == 1, f"se esperaba solo spa.html, hay {len(PLANTILLAS)}"
    assert PLANTILLAS[0].name == "spa.html"


@pytest.mark.parametrize("plantilla", PLANTILLAS, ids=lambda p: p.name)
def test_ningun_comentario_abarca_varias_lineas(plantilla):
    texto = plantilla.read_text(encoding="utf-8")
    rotos = [
        numero
        for numero, linea in enumerate(texto.splitlines(), start=1)
        if "{#" in linea and "#}" not in linea
    ]

    assert not rotos, (
        f"{plantilla.name}: comentario «{{#» sin cerrar en su línea (líneas {rotos}). "
        "Se imprimiría tal cual; usa {% comment %}…{% endcomment %}."
    )


def test_un_comentario_multilinea_se_imprimiria():
    motor = engines["django"]

    assert motor.from_string("A{# en una linea #}B").render({}) == "AB"
    assert "{#" in motor.from_string("A{# en\ndos lineas #}B").render({})


MARCAS_SIN_PROCESAR = ["{{", "{%", "{#"]


@pytest.mark.django_db
def test_la_cascara_no_deja_marcas_de_plantilla(client, django_user_model):
    client.force_login(django_user_model.objects.create_user("ana", password="Contrasena-Larga-1"))

    contenido = client.get(reverse("dashboard")).content.decode()

    for marca in MARCAS_SIN_PROCESAR:
        assert marca not in contenido, f"«{marca}» sin procesar en la cáscara"
    assert '<div id="root">' in contenido
    assert "/static/spa/" in contenido or ":5173" in contenido
    assert 'rel="manifest"' in contenido


@pytest.mark.django_db
def test_la_cascara_no_lleva_ningun_dato_de_quien_la_pide(client, django_user_model):
    usuario = django_user_model.objects.create_user(
        "zacarias", email="zacarias@ejemplo.com", password="Contrasena-Larga-1", first_name="Zoe"
    )
    client.force_login(usuario)

    contenido = client.get(reverse("dashboard")).content.decode()

    for dato in ("zacarias", "Zoe", "ejemplo.com"):
        assert dato not in contenido, f"la cáscara lleva «{dato}», y el service worker la guarda"


@pytest.mark.django_db
def test_la_cascara_trae_lo_que_ios_necesita(client):
    contenido = client.get(reverse("login")).content.decode()

    assert '<meta name="apple-mobile-web-app-capable" content="yes">' in contenido
    assert 'name="apple-mobile-web-app-status-bar-style" content="default"' in contenido
    assert "pwa/apple-touch-icon" in contenido
    assert 'name="app-version"' in contenido
    assert contenido.count('name="theme-color"') == 2
