from django import template

from .. import pwa
from ..vite import en_desarrollo, etiquetas

register = template.Library()


@register.simple_tag(takes_context=True)
def vite(context):
    nonce = ""

    if en_desarrollo():
        peticion = context.get("request")
        nonce = getattr(peticion, "csp_nonce", "") if peticion else ""

    return etiquetas(str(nonce))


@register.simple_tag
def version_de_la_app():
    return pwa.version() if pwa.offline_activo() else "sin-cache"
