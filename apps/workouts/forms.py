from django import forms
from django.utils import timezone

from .models import Exercise, Program, Routine, WorkoutSession
from .taxonomy import BodyPart, Equipment


class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class CustomExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ("name", "body_part", "equipment", "is_bodyweight", "is_unilateral")
        labels = {
            "is_bodyweight": "Es de peso corporal",
            "is_unilateral": "Es unilateral",
        }
        help_texts = {
            "is_bodyweight": (
                "Márcalo si el peso que mueves es el tuyo (dominadas, fondos). Así el tonelaje "
                "se calcula con tu peso corporal y no con cero."
            ),
            "is_unilateral": (
                "Márcalo si se hace un lado y luego el otro. Anotarás las series por lado y el "
                "tonelaje contará los dos."
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["body_part"].choices = BodyPart.choices
        self.fields["equipment"].choices = Equipment.choices

    def clean_name(self):
        nombre = (self.cleaned_data["name"] or "").strip()
        if not nombre:
            raise forms.ValidationError("Ponle un nombre.")
        ya_existe = (
            Exercise.objects.visible_to(self.user)
            .filter(name__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if ya_existe:
            raise forms.ValidationError(
                "Ya tienes un ejercicio con ese nombre, o está en el catálogo."
            )
        return nombre


class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ("date", "notes")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial.setdefault("date", timezone.localdate())
