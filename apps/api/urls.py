from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import auth, avisos, gestion, ia, pantallas, views

router = DefaultRouter()
router.register("ejercicios", views.ExerciseViewSet, basename="api-exercise")
router.register("rutinas", views.RoutineViewSet, basename="api-routine")
router.register("programas", views.ProgramViewSet, basename="api-program")
router.register("dias", views.ScheduleEntryViewSet, basename="api-schedule-entry")
router.register("rutina-ejercicios", views.RoutineExerciseViewSet, basename="api-routine-exercise")
router.register("entrenamientos", views.WorkoutSessionViewSet, basename="api-session")
router.register("series", views.SetLogViewSet, basename="api-set")
router.register("peso", views.BodyWeightEntryViewSet, basename="api-bodyweight")
router.register("notificaciones", views.NotificationViewSet, basename="api-notification")
router.register("metricas", views.MetricCatalogViewSet, basename="api-metric")

gestion_router = DefaultRouter()
gestion_router.register("proveedores", gestion.ProveedorViewSet, basename="api-gestion-proveedor")
gestion_router.register("prompts", gestion.PromptViewSet, basename="api-gestion-prompt")
gestion_router.register("almacenes", gestion.AlmacenViewSet, basename="api-gestion-almacen")
gestion_router.register("documentos", gestion.DocumentoViewSet, basename="api-gestion-documento")
gestion_router.register(
    "programacion", gestion.ProgramacionViewSet, basename="api-gestion-programacion"
)
gestion_router.register(
    "generaciones", gestion.GeneracionViewSet, basename="api-gestion-generacion"
)
gestion_router.register("usuarios", gestion.UsuarioViewSet, basename="api-gestion-usuario")
gestion_router.register("metricas", gestion.MetricaDeGestionViewSet, basename="api-gestion-metrica")

urlpatterns = [
    path("auth/session/", auth.SessionView.as_view(), name="api-session"),
    path("auth/registro/", auth.RegistroView.as_view(), name="api-registro"),
    path("auth/password/", auth.ContrasenaView.as_view(), name="api-password"),
    path("cuenta/", auth.CuentaView.as_view(), name="api-cuenta"),
    path("perfil/opciones/", auth.TaxonomiaDePerfilView.as_view(), name="api-perfil-opciones"),

    path("auth/token/", views.LoginView.as_view(), name="api-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="api-token-verify"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="api-token-blacklist"),

    path("perfil/", views.ProfileView.as_view(), name="api-profile"),

    path("avisos/clave/", avisos.ClaveDeAvisosView.as_view(), name="api-avisos-clave"),
    path("avisos/suscripcion/", avisos.SuscripcionView.as_view(), name="api-avisos-suscripcion"),
    path("mis-metricas/", views.MyMetricsView.as_view(), name="api-my-metrics"),

    path("inicio/", pantallas.InicioView.as_view(), name="api-inicio"),
    path("plan/", pantallas.PlanView.as_view(), name="api-plan"),
    path("mapa-corporal/", pantallas.MapaCorporalView.as_view(), name="api-mapa-corporal"),
    path("progreso/", pantallas.ProgresoView.as_view(), name="api-progreso"),

    path("ia/generar/", ia.GenerarView.as_view(), name="api-ia-generar"),
    path("ia/propuestas/<int:pk>/", ia.PropuestaView.as_view(), name="api-ia-propuesta"),
    path("ia/propuestas/<int:pk>/aceptar/", ia.AceptarView.as_view(), name="api-ia-aceptar"),
    path("ia/propuestas/<int:pk>/descartar/", ia.DescartarView.as_view(), name="api-ia-descartar"),
    path("ia/analisis/", ia.AnalisisView.as_view(), name="api-ia-analisis"),

    path("gestion/resumen/", gestion.ResumenView.as_view(), name="api-gestion-resumen"),
    path("gestion/catalogo/", gestion.CatalogoView.as_view(), name="api-gestion-catalogo"),
    path("gestion/", include(gestion_router.urls)),

    path("", include(router.urls)),
]
