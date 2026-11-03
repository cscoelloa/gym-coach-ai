from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.common.pwa import manifiesto, service_worker
from apps.common.views import spa, spa_publica

SPA_URLS = [
    path("estilos/", spa, name="styleguide"),
    path("", spa, name="dashboard"),
    path("peso/", spa, name="bodyweight_list"),
    path("notificaciones/", spa, name="notification_list"),
    path("ejercicios/", spa, name="exercise_list"),
    path("ejercicios/nuevo/", spa, name="exercise_create"),
    path("ejercicios/<slug:slug>/", spa, name="exercise_detail"),
    path("plan/", spa, name="plan"),
    path("plan/dia/<int:weekday>/", spa, name="schedule_day"),
    path("programas/nuevo/", spa, name="program_create"),
    path("rutinas/nueva/", spa, name="routine_create"),
    path("rutinas/<int:pk>/", spa, name="routine_detail"),
    path("entrenamientos/", spa, name="session_list"),
    path("entrenamientos/<int:pk>/", spa, name="session_detail"),
    path("entrenamientos/<int:pk>/cierre/", spa, name="session_summary"),
    path("progreso/", spa, name="metrics_progress"),
    path("metricas/", spa, name="metrics_catalog"),
    path("ia/generar/", spa, name="ai_generate"),
    path("ia/propuestas/<int:pk>/", spa, name="ai_preview"),
    path("ia/analisis/", spa, name="ai_analysis"),
    path("gestion/", spa, name="gestion"),
    path("gestion/ia/", spa, name="gestion_ia"),
    path("gestion/generaciones/", spa, name="gestion_generaciones"),
    path("gestion/usuarios/", spa, name="gestion_usuarios"),
    path("gestion/catalogo/", spa, name="gestion_catalogo"),
    path("perfil/", spa, name="profile"),
    path("perfil/eliminar/", spa, name="account_delete"),
]

SPA_URLS_PUBLICAS = [
    path("entrar/", spa_publica, name="login"),
    path("registro/", spa_publica, name="register"),
    path("sesion-cerrada/", spa_publica, name="logged_out"),
]

urlpatterns = [
    path("admin/", admin.site.urls),

    path("manifest.webmanifest", manifiesto, name="manifest"),
    path("sw.js", service_worker, name="service_worker"),
    path("api/", include("apps.api.urls")),
    *SPA_URLS,
    *SPA_URLS_PUBLICAS,
    path("", include("apps.accounts.urls")),
    path("", include("apps.workouts.urls")),
    path("", include("apps.bodyweight.urls")),
    path("", include("apps.metrics.urls")),
    path("", include("apps.aiassist.urls")),
    path("", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
