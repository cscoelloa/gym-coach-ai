import json

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_credentials
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.privacy import delete_account, export_data

DESTINO_POR_DEFECTO = "/"


class UsuarioDeSesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "is_staff")
        read_only_fields = fields


def _destino_seguro(peticion, propuesto: str | None) -> str:
    if propuesto and url_has_allowed_host_and_scheme(
        propuesto, allowed_hosts={peticion.get_host()}, require_https=peticion.is_secure()
    ):
        return propuesto
    return DESTINO_POR_DEFECTO


class EntrarSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)
    next = serializers.CharField(required=False, allow_blank=True)


@method_decorator(csrf_protect, name="dispatch")
class SessionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def get_throttles(self):
        self.throttle_scope = "login" if self.request.method == "POST" else "sesion"
        return super().get_throttles()

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No hay sesión iniciada."}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(UsuarioDeSesionSerializer(request.user).data)

    def post(self, request):
        entrada = EntrarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        credenciales = get_credentials(
            username=entrada.validated_data["username"],
            password=entrada.validated_data["password"],
        )

        if not AxesProxyHandler.is_allowed(request, credenciales):
            return Response(
                {
                    "detail": (
                        "Demasiados intentos fallidos. La cuenta queda bloqueada durante una "
                        "hora por seguridad."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario = authenticate(
            request,
            username=entrada.validated_data["username"],
            password=entrada.validated_data["password"],
        )

        if usuario is None:
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, usuario)

        return Response({
            "usuario": UsuarioDeSesionSerializer(usuario).data,
            "redirect": _destino_seguro(request, entrada.validated_data.get("next")),
        })

    def delete(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {"email": {"required": True, "allow_blank": False}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Las dos contraseñas no coinciden."})

        candidato = User(username=attrs["username"], email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidato)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error

        return attrs

    def create(self, datos):
        datos.pop("password2")
        return User.objects.create_user(**datos)


@method_decorator(csrf_protect, name="dispatch")
class RegistroView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializador = RegistroSerializer(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = serializador.save()

        login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")

        return Response(
            {
                "usuario": UsuarioDeSesionSerializer(usuario).data,
                "redirect": "/perfil/",
            },
            status=status.HTTP_201_CREATED,
        )


class CambioDeContrasenaSerializer(serializers.Serializer):
    actual = serializers.CharField(style={"input_type": "password"})
    nueva = serializers.CharField(style={"input_type": "password"})

    def validate_actual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return valor

    def validate_nueva(self, valor):
        try:
            validate_password(valor, user=self.context["request"].user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages)) from error
        return valor


class ContrasenaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializador = CambioDeContrasenaSerializer(
            data=request.data, context={"request": request}
        )
        serializador.is_valid(raise_exception=True)

        request.user.set_password(serializador.validated_data["nueva"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CuentaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contenido = json.dumps(export_data(request.user), ensure_ascii=False, indent=2)

        respuesta = HttpResponse(contenido, content_type="application/json; charset=utf-8")
        nombre = f"project-gym-{request.user.username}-{timezone.localdate()}.json"
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta

    def delete(self, request):
        if str(request.data.get("confirmacion", "")).strip() != request.user.username:
            return Response(
                {"confirmacion": ["Escribe tu nombre de usuario exactamente para confirmar."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resumen = delete_account(request.user)
        logout(request)
        return Response(resumen)


class TaxonomiaDePerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.accounts.models import ExperienceLevel, Goal, Sex
        from apps.workouts.taxonomy import Equipment

        def opciones(choices):
            return [{"valor": valor, "etiqueta": etiqueta} for valor, etiqueta in choices]

        return Response({
            "goal": opciones(Goal.choices),
            "experience_level": opciones(ExperienceLevel.choices),
            "sex": opciones(Sex.choices),
            "available_equipment": opciones(Equipment.choices),
        })
