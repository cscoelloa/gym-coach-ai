from django.db import transaction
from django.db.models import Count, Prefetch
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.models import Metric, UserMetricPreference
from apps.metrics.services import compute, visible_for
from apps.notifications.models import Notification
from apps.workouts import catalog, descanso, focus
from apps.workouts.models import (
    Exercise,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    SetLog,
    Weekday,
    WorkoutSession,
)
from apps.workouts.taxonomy import BodyPart, Equipment

from .pantallas import serie_de_peso
from .permissions import IsOwner
from .serializers import (
    BodyWeightEntrySerializer,
    ComputedMetricSerializer,
    EjercicioPropioSerializer,
    ExerciseSerializer,
    MetricSerializer,
    NotificationSerializer,
    ProfileSerializer,
    ProgramListSerializer,
    ProgramSerializer,
    RoutineExerciseSerializer,
    RoutineListSerializer,
    RoutineSerializer,
    ScheduleEntrySerializer,
    SetLogSerializer,
    WorkoutSessionSerializer,
)

EJERCICIOS_RECIENTES = 60


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class OwnedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def get_queryset(self):
        return self.queryset.filter(**{self.owner_field: self.request.user})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_serializer_class(self):
        return EjercicioPropioSerializer if self.action == "create" else ExerciseSerializer

    def get_queryset(self):
        queryset = catalog.filtrar(
            self.request.user, catalog.filtros_desde(self.request.query_params)
        )
        return queryset.prefetch_related("secondary_muscles")

    def perform_create(self, serializer):
        serializer.save(
            is_global=False,
            created_by=self.request.user,
            external_id="",
            slug=catalog.slug_unico(serializer.validated_data["name"]),
        )

    def create(self, request, *args, **kwargs):
        entrada = self.get_serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        self.perform_create(entrada)
        return Response(
            ExerciseSerializer(entrada.instance).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"])
    def taxonomia(self, request):
        return Response({
            "body_part": [{"valor": v, "etiqueta": e} for v, e in BodyPart.choices],
            "equipment": [{"valor": v, "etiqueta": e} for v, e in Equipment.choices],
        })

    @action(detail=False, methods=["get"])
    def facetas(self, request):
        filtros = catalog.filtros_desde(request.query_params)

        def opciones(campo, choices):
            recuentos = catalog.recuentos_por(request.user, campo, filtros)
            return [
                {"valor": valor, "etiqueta": etiqueta, "n": recuentos[valor]}
                for valor, etiqueta in choices
                if recuentos.get(valor)
            ]

        musculos = catalog.musculos_con_ejercicios(request.user)

        return Response({
            "total": catalog.filtrar(request.user, filtros).count(),
            "body_part": opciones("body_part", BodyPart.choices),
            "equipment": opciones("equipment", Equipment.choices),
            "muscle": [
                {"valor": slug, "etiqueta": etiqueta, "n": n} for slug, etiqueta, n in musculos
            ],
        })


class RoutineViewSet(OwnedModelViewSet):
    queryset = Routine.objects.prefetch_related(
        Prefetch(
            "exercises",
            queryset=RoutineExercise.objects.select_related(
                "exercise", "exercise__target_muscle"
            ).order_by("order", "pk"),
        )
    ).order_by("name", "pk")
    serializer_class = RoutineSerializer

    def get_queryset(self):
        return super().get_queryset().annotate(exercise_count=Count("exercises", distinct=True))

    def get_serializer_class(self):
        return RoutineListSerializer if self.action == "list" else RoutineSerializer


class ProgramViewSet(OwnedModelViewSet):
    queryset = Program.objects.prefetch_related(
        Prefetch(
            "schedule",
            queryset=ScheduleEntry.objects.select_related("routine").order_by("weekday"),
        )
    ).order_by("-is_active", "-created_at", "-pk")
    serializer_class = ProgramSerializer

    def get_serializer_class(self):
        return ProgramListSerializer if self.action == "list" else ProgramSerializer

    def perform_create(self, serializer):
        program = serializer.save(user=self.request.user)
        ScheduleEntry.objects.bulk_create([
            ScheduleEntry(program=program, weekday=weekday) for weekday, _ in Weekday.choices
        ])
        program.activate()

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        program = self.get_object()
        program.activate()
        return Response(ProgramListSerializer(program).data)


class ScheduleEntryViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ScheduleEntry.objects.select_related("program", "routine")
    serializer_class = ScheduleEntrySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = self.queryset.filter(program__user=self.request.user)
        if program_id := self.request.query_params.get("program"):
            queryset = queryset.filter(program_id=program_id)
        return queryset.order_by("program", "weekday")


class RoutineExerciseViewSet(viewsets.ModelViewSet):
    queryset = RoutineExercise.objects.select_related("routine", "exercise")
    serializer_class = RoutineExerciseSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(
            routine__user=self.request.user
        ).order_by("routine", "order", "pk")

    def perform_create(self, serializer):
        datos = serializer.validated_data
        rutina = datos["routine"]

        if "order" not in datos:
            ultimo = rutina.exercises.order_by("-order").first()
            datos["order"] = (ultimo.order + 1) if ultimo else 0

        if "rest_seconds" not in datos:
            datos["rest_seconds"] = datos["exercise"].default_rest

        serializer.save()

    @action(detail=True, methods=["post"])
    def mover(self, request, pk=None):
        item = self.get_object()
        direccion = request.data.get("direccion")
        if direccion not in ("subir", "bajar"):
            return Response(
                {"direccion": "Tiene que ser «subir» o «bajar»."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hermanos = list(item.routine.exercises.order_by("order", "pk"))
        posicion = next(i for i, x in enumerate(hermanos) if x.pk == item.pk)
        destino = posicion - 1 if direccion == "subir" else posicion + 1

        if 0 <= destino < len(hermanos):
            hermanos[posicion], hermanos[destino] = hermanos[destino], hermanos[posicion]
            for indice, hermano in enumerate(hermanos):
                if hermano.order != indice:
                    hermano.order = indice
                    hermano.save(update_fields=["order"])

        return Response(
            RoutineExerciseSerializer(
                item.routine.exercises.select_related("exercise").order_by("order", "pk"),
                many=True,
                context=self.get_serializer_context(),
            ).data
        )


class WorkoutSessionViewSet(OwnedModelViewSet):
    queryset = (
        WorkoutSession.objects.select_related("routine")
        .prefetch_related("sets__exercise")
        .annotate(set_count=Count("sets"))
        .order_by("-date", "-pk")
    )
    serializer_class = WorkoutSessionSerializer

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            date=serializer.validated_data.get("date") or timezone.localdate(),
            started_at=timezone.now(),
        )

    @action(detail=True, methods=["get"])
    def foco(self, request, pk=None):
        sesion = self.get_object()
        try:
            indice = int(request.query_params["ejercicio"])
        except KeyError:
            indice = None
        except (TypeError, ValueError):
            indice = 1

        return Response(focus.contexto_de_foco(request.user, sesion, indice))

    @action(detail=True, methods=["post"])
    def descanso(self, request, pk=None):
        sesion = self.get_object()
        accion = request.data.get("accion")
        if accion not in ("alargar", "saltar"):
            return Response(
                {"accion": ["Tiene que ser «alargar» o «saltar»."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ahora = timezone.now()
        with transaction.atomic():
            bloqueada = WorkoutSession.objects.select_for_update().get(pk=sesion.pk)
            if accion == "alargar":
                descanso.alargar(bloqueada, ahora)
            else:
                descanso.saltar(bloqueada)

        return Response({"descanso": focus.estado_del_descanso(bloqueada, ahora)})

    @action(detail=True, methods=["get"])
    def resumen(self, request, pk=None):
        return Response(focus.resumen_de_cierre(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        sesion = self.get_object()
        if sesion.finished_at is None:
            sesion.finished_at = timezone.now()
            descanso.limpiar(sesion)
            sesion.save(update_fields=["finished_at", "rest_ends_at", "rest_seconds"])

        return Response(focus.resumen_de_cierre(request.user, sesion))

    @action(detail=False, methods=["get"])
    def ejercicios_recientes(self, request):
        usados = SetLog.objects.filter(session__user=request.user).values_list(
            "exercise_id", flat=True
        )
        planificados = RoutineExercise.objects.filter(
            routine__user=request.user
        ).values_list("exercise_id", flat=True)

        ejercicios = Exercise.objects.filter(
            pk__in=set(usados) | set(planificados)
        ).order_by("name")[:EJERCICIOS_RECIENTES]

        return Response(
            [{"id": e.pk, "nombre": e.name} for e in ejercicios]
        )


class SetLogViewSet(viewsets.ModelViewSet):
    queryset = SetLog.objects.select_related("session", "exercise")
    serializer_class = SetLogSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = self.queryset.filter(session__user=self.request.user)
        if session_id := self.request.query_params.get("session"):
            queryset = queryset.filter(session_id=session_id)
        return queryset.order_by("session", "exercise__name", "set_number")

    def perform_create(self, serializer):
        datos = serializer.validated_data
        with transaction.atomic():
            sesion = WorkoutSession.objects.select_for_update().get(pk=datos["session"].pk)
            if "set_number" not in datos:
                datos["set_number"] = SetLog.siguiente_numero(sesion.pk, datos["exercise"].pk)
            serie = serializer.save()

            ahora = timezone.now()
            descanso.tras_registrar(sesion, serie, ahora)
            self.descanso_en_curso = focus.estado_del_descanso(sesion, ahora)

    def create(self, request, *args, **kwargs):
        respuesta = super().create(request, *args, **kwargs)
        respuesta.data["descanso"] = getattr(self, "descanso_en_curso", None)
        return respuesta

    def perform_destroy(self, instance):
        with transaction.atomic():
            WorkoutSession.objects.select_for_update().get(pk=instance.session_id)
            sesion, ejercicio = instance.session_id, instance.exercise_id
            instance.delete()
            SetLog.renumerar(sesion, ejercicio)


class BodyWeightEntryViewSet(OwnedModelViewSet):
    queryset = BodyWeightEntry.objects.order_by("-date", "-pk")
    serializer_class = BodyWeightEntrySerializer

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        pesos = self.get_queryset()
        ultimo = pesos.first()
        anterior = pesos.exclude(pk=ultimo.pk).first() if ultimo else None
        serie = serie_de_peso(request.user)

        return Response({
            "ultimo": BodyWeightEntrySerializer(ultimo).data if ultimo else None,
            "cambio": (
                float(ultimo.weight_kg - anterior.weight_kg) if ultimo and anterior else None
            ),
            "objetivo": request.user.get_goal_display(),
            "meta_kg": (
                float(request.user.target_weight_kg) if request.user.target_weight_kg else None
            ),
            "serie": serie if len(serie["values"]) >= 2 else None,
        })


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Notification.objects.order_by("-created_at", "-pk")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.request.query_params.get("unread") == "true":
            queryset = queryset.filter(is_read=False)
        return queryset

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        actualizadas = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": actualizadas})


class MetricCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Metric.objects.filter(is_active=True).order_by("category", "order")
    serializer_class = MetricSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "key"
    pagination_class = None

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "visibles": set(visible_for(self.request.user))}

    @action(detail=False, methods=["put"])
    def preferencias(self, request):
        pedidas = request.data.get("keys")
        if not isinstance(pedidas, list):
            return Response(
                {"keys": ["Se espera una lista de claves de métrica."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        catalogo = list(self.get_queryset())
        conocidas = {metrica.key for metrica in catalogo}
        desconocidas = sorted(set(map(str, pedidas)) - conocidas)
        if desconocidas:
            return Response(
                {"keys": [f"No existen estas métricas: {', '.join(desconocidas)}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        elegidas = set(map(str, pedidas))
        for metrica in catalogo:
            UserMetricPreference.objects.update_or_create(
                user=request.user,
                metric=metrica,
                defaults={"is_visible": metrica.key in elegidas},
            )

        return Response({"visibles": sorted(elegidas)})


class MyMetricsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "metrics"

    def get(self, request):
        keys = request.query_params.getlist("key") or visible_for(request.user)
        weeks = _as_int(request.query_params.get("weeks"), default=12, low=1, high=104)

        computed = compute(request.user, keys=keys, weeks=weeks)
        return Response(ComputedMetricSerializer(computed, many=True).data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


def _as_int(value, *, default, low, high):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(number, high))
