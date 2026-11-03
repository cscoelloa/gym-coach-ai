from django.core.management.base import BaseCommand

from apps.aiassist.fields import encrypt
from apps.aiassist.models import AIProviderConfig

ENCRYPTED_FIELDS = [(AIProviderConfig, ["api_key"])]


class Command(BaseCommand):
    help = "Re-cifra los secretos con la primera clave de FIELD_ENCRYPTION_KEYS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Informa de cuántos valores se re-cifrarían, sin tocar nada.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total = 0

        for model, field_names in ENCRYPTED_FIELDS:
            for instance in model.objects.all():
                changed = []
                for field_name in field_names:
                    plaintext = getattr(instance, field_name)
                    if not plaintext:
                        continue
                    if not dry_run:
                        model.objects.filter(pk=instance.pk).update(
                            **{field_name: encrypt(plaintext)}
                        )
                    changed.append(field_name)

                if changed:
                    total += len(changed)
                    self.stdout.write(f"  {model.__name__}#{instance.pk}: {', '.join(changed)}")

        verbo = "se re-cifrarían" if dry_run else "re-cifrados"
        self.stdout.write(self.style.SUCCESS(f"{total} valores {verbo}."))
        if not dry_run and total:
            self.stdout.write(
                "Ya puedes retirar la clave antigua de FIELD_ENCRYPTION_KEYS y reiniciar."
            )
