from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def spa_publica(request, **_parametros):
    return render(request, "spa.html")


@login_required
@ensure_csrf_cookie
def spa(request, **_parametros):
    return render(request, "spa.html")
