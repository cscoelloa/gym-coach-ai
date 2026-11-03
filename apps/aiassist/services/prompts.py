import re
import unicodedata

from django.conf import settings
from django.template import Context, Template

from ..models import PromptKey, PromptTemplate

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class MissingPrompt(Exception):
    pass


def sanitize(text: str, *, max_chars: int) -> str:
    if not text:
        return ""
    cleaned = unicodedata.normalize("NFC", str(text))
    cleaned = _CONTROL_CHARS.sub("", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "…"
    return cleaned


def as_data(text: str, tag: str, *, max_chars: int | None = None) -> str:
    limit = max_chars or settings.PROMPT_MAX_NOTES_CHARS
    cleaned = sanitize(text, max_chars=limit)
    if not cleaned:
        return ""
    cleaned = cleaned.replace(f"</{tag}>", f"<_{tag}>")
    return f"<{tag}>\n{cleaned}\n</{tag}>"


def get_prompt(key: str) -> PromptTemplate:
    prompt = PromptTemplate.objects.filter(key=key, is_active=True).order_by("-version").first()
    if prompt is None:
        raise MissingPrompt(
            f"No hay ninguna plantilla activa para «{PromptKey(key).label}». "
            "Créala en /admin/ → Prompts, o ejecuta `python manage.py seed_prompts`."
        )
    return prompt


def render(prompt: PromptTemplate, context: dict) -> tuple[str, str]:
    system = Template(prompt.system_prompt).render(Context(context, autoescape=False))
    user = Template(prompt.user_template).render(Context(context, autoescape=False))
    return system.strip(), user.strip()


def format_profile(user) -> str:
    profile = user.ai_profile()
    lines = [
        f"Objetivo: {profile['objetivo']}",
        f"Nivel: {profile['nivel']}",
    ]
    if profile["edad"]:
        lines.append(f"Edad: {profile['edad']} años")
    if profile["altura_cm"]:
        lines.append(f"Altura: {profile['altura_cm']} cm")
    if profile["peso_objetivo_kg"]:
        lines.append(f"Peso objetivo: {profile['peso_objetivo_kg']} kg")
    return "\n".join(lines)


def format_equipment(user) -> str:
    from apps.workouts.taxonomy import Equipment

    codes = user.available_equipment or []
    if not codes:
        return "Sin restricción: se asume gimnasio completo."
    labels = dict(Equipment.choices)
    return ", ".join(labels.get(code, code) for code in codes)


def format_metrics(computed) -> str:
    if not computed:
        return "Sin historial suficiente todavía."

    lines = []
    for item in computed:
        if item.result.is_empty:
            continue

        value = item.result.value
        header = f"- {item.spec.label}"
        if value is not None:
            header += f": {value} {item.spec.unit}".rstrip()

        if item.result.coverage < 1:
            header += f" [cobertura {item.result.coverage_pct}%: dato parcial]"
        lines.append(header)

        for point in item.result.series[:8]:
            lines.append(f"    · {point['label']}: {point['value']}")
        for row in item.result.rows[:8]:
            lines.append("    · " + " | ".join(str(cell) for cell in row))

    return "\n".join(lines) if lines else "Sin historial suficiente todavía."


def format_candidates(exercises) -> str:
    return "\n".join(
        f"{exercise.external_id} — {exercise.name} "
        f"({exercise.get_body_part_display()}, {exercise.get_equipment_display()}, "
        f"objetivo: {exercise.target_muscle.name if exercise.target_muscle else '—'})"
        for exercise in exercises
    )
