from django.db.models import Count, Q
from django.utils.text import slugify

from .models import Exercise, MuscleGroup
from .taxonomy import muscle_label

TAMANO_DE_PAGINA = 24

CAMPOS = ("q", "body_part", "equipment", "muscle")

SOLO_MI_MATERIAL = "mi_material"


def filtros_desde(params) -> dict[str, str]:
    filtros = {campo: (params.get(campo) or "").strip() for campo in CAMPOS}
    if params.get(SOLO_MI_MATERIAL):
        filtros[SOLO_MI_MATERIAL] = "1"
    return filtros


def filtrar(user, filtros: dict[str, str]):
    queryset = Exercise.objects.visible_to(user).select_related("target_muscle")

    if filtros.get(SOLO_MI_MATERIAL) and not filtros.get("equipment"):
        material = getattr(user, "available_equipment", None) or []
        if material:
            queryset = queryset.filter(equipment__in=material)

    if nombre := filtros.get("q"):
        queryset = queryset.filter(name__icontains=nombre)
    if parte := filtros.get("body_part"):
        queryset = queryset.filter(body_part=parte)
    if material := filtros.get("equipment"):
        queryset = queryset.filter(equipment=material)
    if musculo := filtros.get("muscle"):
        queryset = queryset.filter(
            Q(target_muscle__slug=musculo) | Q(secondary_muscles__slug=musculo)
        ).distinct()

    return queryset.order_by("name", "pk")


def musculos_con_ejercicios(user) -> list[tuple[str, str, int]]:
    visibles = Exercise.objects.visible_to(user)
    filas = (
        MuscleGroup.objects.annotate(
            n=Count("primary_exercises", filter=Q(primary_exercises__in=visibles), distinct=True)
            + Count(
                "secondary_exercises", filter=Q(secondary_exercises__in=visibles), distinct=True
            )
        )
        .filter(n__gt=0)
        .order_by("-n", "slug")
        .values_list("slug", "n")
    )
    return [(slug, muscle_label(slug), n) for slug, n in filas]


def musculos_entrenables(user, *, minimo: int = 3) -> list[tuple[str, str, int]]:
    visibles = Exercise.objects.visible_to(user).exclude(body_part="cardio")
    if equipamiento := (user.available_equipment or []):
        visibles = visibles.filter(equipment__in=equipamiento)

    filas = (
        MuscleGroup.objects.annotate(
            n=Count("primary_exercises", filter=Q(primary_exercises__in=visibles), distinct=True)
        )
        .filter(n__gte=minimo)
        .order_by("-n", "slug")
        .values_list("slug", "n")
    )
    return [(slug, muscle_label(slug), n) for slug, n in filas]


def slug_unico(nombre: str) -> str:
    base = slugify(nombre)[:200] or "ejercicio"
    slug = base
    contador = 2
    while Exercise.objects.filter(slug=slug).exists():
        slug = f"{base}-{contador}"
        contador += 1
    return slug


def recuentos_por(user, campo: str, filtros: dict[str, str]) -> dict[str, int]:
    otros = {clave: valor for clave, valor in filtros.items() if clave != campo}

    base = filtrar(user, otros).order_by()

    return dict(
        base.values_list(campo).annotate(n=Count("pk", distinct=True)).values_list(campo, "n")
    )
