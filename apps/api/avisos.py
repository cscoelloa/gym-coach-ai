import base64
import binascii

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.notifications import push
from apps.notifications.models import SuscripcionPush

MAXIMO_POR_USUARIO = 10


def _base64url(valor: str) -> bytes:
    return base64.urlsafe_b64decode(valor + "=" * (-len(valor) % 4))


class SuscripcionSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=1000)
    p256dh = serializers.CharField(max_length=200)
    auth = serializers.CharField(max_length=100)

    def to_internal_value(self, data):
        claves = data.get("keys") if isinstance(data, dict) else None
        if isinstance(claves, dict):
            data = {**data, "p256dh": claves.get("p256dh"), "auth": claves.get("auth")}
        return super().to_internal_value(data)

    def validate_endpoint(self, valor):
        if not push.servicio_permitido(valor):
            raise serializers.ValidationError("Ese servicio de push no está permitido.")
        return valor

    def validate_p256dh(self, valor):
        try:
            crudo = _base64url(valor)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError("Clave no válida.") from None
        if len(crudo) != 65 or crudo[0] != 4:
            raise serializers.ValidationError("Clave no válida.")
        return valor

    def validate_auth(self, valor):
        try:
            crudo = _base64url(valor)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError("Clave no válida.") from None
        if len(crudo) != 16:
            raise serializers.ValidationError("Clave no válida.")
        return valor


class ClaveDeAvisosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clave = push.clave_publica()
        return Response({"activo": clave is not None, "clave": clave})


class SuscripcionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "avisos"

    def post(self, request):
        if not push.activo():
            return Response(
                {"detail": "Los avisos no están configurados en este servidor."},
                status=status.HTTP_409_CONFLICT,
            )

        datos = SuscripcionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)

        with transaction.atomic():
            SuscripcionPush.objects.update_or_create(
                endpoint=datos.validated_data["endpoint"],
                defaults={
                    "user": request.user,
                    "p256dh": datos.validated_data["p256dh"],
                    "auth": datos.validated_data["auth"],
                },
            )
            mias = SuscripcionPush.objects.filter(user=request.user).order_by("-creada")
            sobrantes = list(mias.values_list("pk", flat=True)[MAXIMO_POR_USUARIO:])
            SuscripcionPush.objects.filter(pk__in=sobrantes).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        endpoint = request.data.get("endpoint") if isinstance(request.data, dict) else None
        if endpoint:
            SuscripcionPush.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
