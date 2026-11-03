import json
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.workouts.models import Exercise, MuscleGroup

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "id", "name", "category", "body_part", "equipment", "instructions",
            "instruction_steps", "muscle_group", "secondary_muscles", "target",
            "media_id", "image", "gif_url", "attribution", "created_at",
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^[0-9]{4}$"},
            "name": {"type": "string", "minLength": 1},
            "body_part": {
                "enum": [
                    "back", "cardio", "chest", "lower arms", "lower legs",
                    "neck", "shoulders", "upper arms", "upper legs", "waist",
                ]
            },
            "image": {"type": "string", "pattern": r"^images/.+\.(jpg|jpeg|png)$"},
            "gif_url": {"type": "string", "pattern": r"^videos/.+\.gif$"},
        },
    },
}

LANGS = ["en", "es", "it", "tr", "ru", "zh", "hi", "pl", "ko", "fr"]

ATTRIBUTION = "© Gym visual — https://gymvisual.com/"


def make_record(external_id="0001", **overrides):
    record = {
        "id": external_id,
        "name": f"Ejercicio {external_id}",
        "category": "waist",
        "body_part": "waist",
        "equipment": "body weight",
        "instructions": {lang: f"texto {lang}" for lang in LANGS},
        "instruction_steps": {lang: [f"paso 1 en {lang}", f"paso 2 en {lang}"] for lang in LANGS},
        "muscle_group": "quadriceps",
        "secondary_muscles": ["latissimus dorsi", "trapezius"],
        "target": "abs",
        "media_id": f"media-{external_id}",
        "image": f"images/{external_id}-abc.jpg",
        "gif_url": f"videos/{external_id}-abc.gif",
        "attribution": ATTRIBUTION,
        "created_at": "2026-03-18T12:31:32.854798+00:00",
    }
    record.update(overrides)
    return record


@pytest.fixture
def dataset(tmp_path):
    def _build(records, with_media=True):
        root = tmp_path / "dataset"
        (root / "data").mkdir(parents=True, exist_ok=True)
        (root / "data" / "exercises.json").write_text(
            json.dumps(records, ensure_ascii=False), encoding="utf-8"
        )
        (root / "data" / "exercises.schema.json").write_text(
            json.dumps(SCHEMA), encoding="utf-8"
        )
        if with_media:
            (root / "images").mkdir(exist_ok=True)
            (root / "videos").mkdir(exist_ok=True)
            for record in records:
                (root / record["image"]).write_bytes(b"jpg")
                (root / record["gif_url"]).write_bytes(b"gif")
        return root

    return _build


@pytest.mark.django_db
def test_importa_y_normaliza_musculos(dataset):
    root = dataset([make_record("0001")])

    call_command("import_catalog", source=str(root), skip_media=True)

    exercise = Exercise.objects.get(external_id="0001")
    assert exercise.body_part == "waist"
    assert exercise.is_bodyweight is True
    assert exercise.is_cardio is False
    assert exercise.target_muscle.slug == "abs"

    secundarios = set(exercise.secondary_muscles.values_list("slug", flat=True))
    assert secundarios == {"quads", "lats", "traps"}
    assert not MuscleGroup.objects.filter(slug__in=["quadriceps", "latissimus-dorsi", "trapezius"])


@pytest.mark.django_db
def test_guarda_atribucion_y_los_diez_idiomas(dataset):
    root = dataset([make_record("0002")])

    call_command("import_catalog", source=str(root), skip_media=True)

    exercise = Exercise.objects.get(external_id="0002")
    assert exercise.attribution == ATTRIBUTION
    assert sorted(exercise.instruction_steps) == sorted(LANGS)
    assert exercise.steps("es") == ["paso 1 en es", "paso 2 en es"]
    assert exercise.steps("xx") == ["paso 1 en en", "paso 2 en en"]


@pytest.mark.django_db
def test_es_idempotente(dataset):
    root = dataset([make_record("0003"), make_record("0004")])

    call_command("import_catalog", source=str(root), skip_media=True)
    call_command("import_catalog", source=str(root), skip_media=True)

    assert Exercise.objects.count() == 2


@pytest.mark.django_db
def test_actualiza_en_vez_de_duplicar(dataset):
    root = dataset([make_record("0005", name="Nombre viejo")])
    call_command("import_catalog", source=str(root), skip_media=True)

    root = dataset([make_record("0005", name="Nombre nuevo")])
    call_command("import_catalog", source=str(root), skip_media=True)

    assert Exercise.objects.count() == 1
    assert Exercise.objects.get(external_id="0005").name == "Nombre nuevo"


@pytest.mark.django_db
def test_falla_en_bloque_si_el_esquema_no_valida(dataset):
    root = dataset([make_record("0006"), make_record("bad-id")], with_media=False)

    with pytest.raises(CommandError, match="esquema"):
        call_command("import_catalog", source=str(root), skip_media=True)

    assert Exercise.objects.count() == 0


@pytest.mark.django_db
def test_falla_si_no_encuentra_el_dataset(tmp_path):
    with pytest.raises(CommandError, match="clonado"):
        call_command("import_catalog", source=str(tmp_path / "no-existe"), skip_media=True)


@pytest.mark.django_db
def test_copia_el_material_visual(dataset, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    root = dataset([make_record("0007")])

    call_command("import_catalog", source=str(root))

    exercise = Exercise.objects.get(external_id="0007")
    assert exercise.image.name == "exercises/images/0007-abc.jpg"
    assert exercise.animation.name == "exercises/animations/0007-abc.gif"
    assert (Path(settings.MEDIA_ROOT) / exercise.image.name).exists()
    assert (Path(settings.MEDIA_ROOT) / exercise.animation.name).exists()


@pytest.mark.django_db
def test_avisa_si_falta_media_en_disco(dataset, settings, tmp_path, capsys):
    settings.MEDIA_ROOT = tmp_path / "media"
    root = dataset([make_record("0008")], with_media=False)
    (root / "images").mkdir()
    (root / "videos").mkdir()

    call_command("import_catalog", source=str(root))

    salida = capsys.readouterr().out
    assert "sin archivo de media" in salida
    assert Exercise.objects.filter(external_id="0008").exists()


@pytest.mark.django_db
def test_reimportar_no_vuelve_a_subir_lo_que_ya_esta(dataset, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    root = dataset([make_record("0010")])

    call_command("import_catalog", source=str(root))
    ruta = Path(settings.MEDIA_ROOT) / "exercises/images/0010-abc.jpg"
    primera_vez = ruta.stat().st_mtime_ns

    call_command("import_catalog", source=str(root))

    assert ruta.stat().st_mtime_ns == primera_vez, "se ha vuelto a escribir el mismo archivo"
    assert Exercise.objects.get(external_id="0010").image.name == "exercises/images/0010-abc.jpg"


@pytest.mark.django_db
def test_marca_cardio(dataset):
    root = dataset([make_record("0009", body_part="cardio", equipment="stationary bike")])

    call_command("import_catalog", source=str(root), skip_media=True)

    exercise = Exercise.objects.get(external_id="0009")
    assert exercise.is_cardio is True
    assert exercise.is_bodyweight is False


@pytest.mark.django_db
def test_dice_a_donde_suben_los_archivos(dataset, settings, tmp_path, capsys):
    settings.MEDIA_ROOT = tmp_path / "media"
    root = dataset([make_record("0011")])

    call_command("import_catalog", source=str(root))

    salida = capsys.readouterr().out
    assert "Los archivos van a:" in salida
    assert "disco local" in salida
    assert str(tmp_path) in salida


@pytest.mark.django_db
def test_con_skip_media_no_anuncia_ningun_destino(dataset):
    root = dataset([make_record("0012")])

    call_command("import_catalog", source=str(root), skip_media=True)


@pytest.mark.django_db
def test_informa_del_avance_mientras_sube(dataset, settings, tmp_path, capsys):
    settings.MEDIA_ROOT = tmp_path / "media"
    root = dataset([make_record(f"{n:04d}") for n in range(1, 61)])

    call_command("import_catalog", source=str(root))

    salida = capsys.readouterr().out
    assert "50/60 ejercicios" in salida
    assert "60/60 ejercicios" in salida, (
        "el último tramo también se informa, aunque no sea múltiplo"
    )


@pytest.mark.django_db
def test_sin_subida_no_informa_del_avance(dataset):
    root = dataset([make_record(f"{n:04d}") for n in range(1, 61)])

    call_command("import_catalog", source=str(root), skip_media=True)
