import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from jsonschema import Draft202012Validator

from apps.workouts.models import Exercise, MuscleGroup
from apps.workouts.taxonomy import canonical_muscle

IMAGES_SUBDIR = "exercises/images"
ANIMATIONS_SUBDIR = "exercises/animations"

PROGRESS_EVERY = 50


class Command(BaseCommand):
    help = "Importa el catálogo de ejercicios (datos + imágenes + animaciones)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            help="Raíz del dataset clonado (la carpeta que contiene data/, images/ y videos/).",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Importa solo los datos, sin copiar imágenes ni animaciones.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Importa solo los N primeros registros (para pruebas).",
        )

    def handle(self, *args, **options):
        source = Path(options["source"]).resolve()

        if not options["skip_media"]:
            self.stdout.write(f"Los archivos van a: {self._media_target()}")

        records = self._load_and_validate(source)

        if options["limit"]:
            records = records[: options["limit"]]

        created = updated = 0
        missing_media = []
        total = len(records)

        with transaction.atomic():
            muscles = self._ensure_muscles(records)

            for indice, record in enumerate(records, start=1):
                was_created, media_problem = self._import_one(
                    record,
                    muscles=muscles,
                    source=source,
                    skip_media=options["skip_media"],
                )
                created += was_created
                updated += not was_created
                if media_problem:
                    missing_media.append(media_problem)

                if not options["skip_media"] and (indice % PROGRESS_EVERY == 0 or indice == total):
                    self.stdout.write(f"  {indice}/{total} ejercicios")
                    self.stdout.flush()

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo importado: {created} creados, {updated} actualizados, "
                f"{MuscleGroup.objects.count()} grupos musculares."
            )
        )
        if missing_media:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(missing_media)} ejercicios sin archivo de media en disco: "
                    + ", ".join(missing_media[:10])
                    + ("…" if len(missing_media) > 10 else "")
                )
            )


    def _media_target(self) -> str:
        bucket = getattr(default_storage, "bucket_name", None)
        if bucket:
            dominio = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "")
            destino = f"https://{dominio}" if dominio else "sin dominio público configurado"
            return f"bucket «{bucket}» ({destino})"
        return f"disco local, {getattr(settings, 'MEDIA_ROOT', '?')}"

    def _load_and_validate(self, source: Path) -> list[dict]:
        data_file = source / "data" / "exercises.json"
        schema_file = source / "data" / "exercises.schema.json"

        if not data_file.exists():
            raise CommandError(
                f"No se encontró {data_file}. ¿Está clonado el dataset? "
                "Ver el README"
            )

        records = json.loads(data_file.read_text(encoding="utf-8"))

        if schema_file.exists():
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            errors = sorted(
                Draft202012Validator(schema).iter_errors(records), key=lambda e: list(e.path)
            )
            if errors:
                detail = "\n".join(
                    f"  - {'/'.join(str(p) for p in e.path) or '(raíz)'}: {e.message}"
                    for e in errors[:10]
                )
                raise CommandError(
                    f"El dataset no cumple su propio esquema ({len(errors)} errores). "
                    f"Probablemente cambió el formato de origen.\n{detail}"
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No hay exercises.schema.json; se importa sin validar. Revisa el resultado."
                )
            )

        self.stdout.write(f"{len(records)} registros validados.")
        return records

    def _ensure_muscles(self, records: list[dict]) -> dict[str, MuscleGroup]:
        names = set()
        for record in records:
            names.add(canonical_muscle(record["target"]))
            names.add(canonical_muscle(record["muscle_group"]))
            names.update(canonical_muscle(m) for m in record.get("secondary_muscles", []))
        names.discard("")

        return {name: MuscleGroup.from_canonical(name) for name in sorted(names)}

    def _import_one(self, record, *, muscles, source, skip_media):
        external_id = record["id"]
        target = muscles.get(canonical_muscle(record["target"]))

        secondary_names = {canonical_muscle(m) for m in record.get("secondary_muscles", [])}
        secondary_names.add(canonical_muscle(record["muscle_group"]))
        secondary_names.discard(canonical_muscle(record["target"]))
        secondary_names.discard("")

        exercise, was_created = Exercise.objects.update_or_create(
            external_id=external_id,
            defaults={
                "name": record["name"],
                "slug": slugify(f"{record['name']}-{external_id}")[:220],
                "category": record.get("category", ""),
                "body_part": record["body_part"],
                "equipment": record.get("equipment", ""),
                "target_muscle": target,
                "instruction_steps": record.get("instruction_steps", {}),
                "attribution": record.get("attribution", ""),
                "is_cardio": record["body_part"] == "cardio",
                "is_bodyweight": record.get("equipment") == "body weight",
                "is_global": True,
            },
        )
        exercise.secondary_muscles.set(
            [muscles[name] for name in secondary_names if name in muscles]
        )

        media_problem = None
        if not skip_media:
            media_problem = self._copy_media(record, exercise, source)

        return was_created, media_problem

    def _copy_media(self, record, exercise, source: Path) -> str | None:
        missing = False

        for field, rel_path, subdir in (
            ("image", record.get("image"), IMAGES_SUBDIR),
            ("animation", record.get("gif_url"), ANIMATIONS_SUBDIR),
        ):
            if not rel_path:
                missing = True
                continue

            filename = Path(rel_path).name
            origin = source / rel_path
            if not origin.exists():
                missing = True
                continue

            storage_path = f"{subdir}/{filename}"
            if not default_storage.exists(storage_path):
                with origin.open("rb") as handle:
                    default_storage.save(storage_path, File(handle))

            setattr(exercise, field, storage_path)

        exercise.save(update_fields=["image", "animation"])
        return record["id"] if missing else None
