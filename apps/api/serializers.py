from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.loads import tonelaje_simple
from apps.metrics.models import Metric
from apps.notifications.models import Notification
from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    SetLog,
    WorkoutSession,
)


class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = ("slug", "name")


class ExerciseSerializer(serializers.ModelSerializer):
    target_muscle = MuscleGroupSerializer(read_only=True)
    secondary_muscles = MuscleGroupSerializer(many=True, read_only=True)
    body_part_label = serializers.CharField(source="get_body_part_display", read_only=True)
    equipment_label = serializers.CharField(source="get_equipment_display", read_only=True)
    steps = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = (
            "id", "external_id", "name", "slug", "body_part", "body_part_label",
            "equipment", "equipment_label", "target_muscle", "secondary_muscles",
            "is_cardio", "is_bodyweight", "image", "animation", "attribution", "steps",
        )

    def get_steps(self, obj):
        return obj.steps(self.context.get("lang", "es"))


class EjercicioPropioSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.workouts.models import Exercise as _Exercise

        model = _Exercise
        fields = ("name", "body_part", "equipment", "is_bodyweight", "is_unilateral")

    def validate_name(self, valor):
        from apps.workouts.models import Exercise as _Exercise

        nombre = (valor or "").strip()
        if not nombre:
            raise serializers.ValidationError("Ponle un nombre.")

        ya_existe = (
            _Exercise.objects.visible_to(self.context["request"].user)
            .filter(name__iexact=nombre)
            .exists()
        )
        if ya_existe:
            raise serializers.ValidationError(
                "Ya tienes un ejercicio con ese nombre, o está en el catálogo."
            )
        return nombre


class RoutineExerciseSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source="exercise", read_only=True)

    class Meta:
        model = RoutineExercise
        fields = (
            "id", "routine", "exercise", "exercise_detail", "order",
            "target_sets", "target_reps_min", "target_reps_max", "rest_seconds",
        )

    def validate_routine(self, value):
        if value.user != self.context["request"].user:
            raise serializers.ValidationError("Esa rutina no es tuya.")
        return value

    def validate_exercise(self, value):
        if not Exercise.objects.visible_to(self.context["request"].user).filter(
            pk=value.pk
        ).exists():
            raise serializers.ValidationError("Ese ejercicio no existe.")
        return value

    def validate(self, attrs):
        minimo = attrs.get("target_reps_min", getattr(self.instance, "target_reps_min", None))
        maximo = attrs.get("target_reps_max", getattr(self.instance, "target_reps_max", None))

        if minimo and maximo and minimo > maximo:
            attrs["target_reps_max"] = minimo

        return attrs


class RoutineDraftExerciseSerializer(RoutineExerciseSerializer):
    id = serializers.IntegerField(required=False, min_value=1)

    class Meta(RoutineExerciseSerializer.Meta):
        fields = (
            "id", "exercise", "target_sets", "target_reps_min", "target_reps_max",
            "rest_seconds",
        )

    def validate(self, attrs):
        missing = {
            field: "Este campo es obligatorio al guardar la lista completa."
            for field in self.Meta.fields if field != "id" and field not in attrs
        }
        if missing:
            raise serializers.ValidationError(missing)
        return super().validate(attrs)


class RoutineSerializer(serializers.ModelSerializer):
    exercises = RoutineDraftExerciseSerializer(many=True, required=False, write_only=True)
    source_label = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = Routine
        fields = ("id", "name", "description", "source", "source_label",
                  "created_at", "exercises")
        read_only_fields = ("source", "created_at")

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["exercises"] = RoutineExerciseSerializer(
            instance.exercises.all(), many=True, context=self.context,
        ).data
        return result

    def validate_exercises(self, rows):
        ids = [row["id"] for row in rows if "id" in row]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Un elemento de la rutina está repetido.")
        owned = (
            set(self.instance.exercises.values_list("id", flat=True)) if self.instance else set()
        )
        if not set(ids).issubset(owned):
            raise NotFound("Ese elemento no existe.")
        return rows

    @transaction.atomic
    def create(self, validated_data):
        rows = validated_data.pop("exercises", [])
        routine = super().create(validated_data)
        self._save_rows(routine, rows)
        return routine

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Routine.objects.select_for_update().get(pk=instance.pk, user=instance.user)
        rows = validated_data.pop("exercises", None)
        instance = super().update(instance, validated_data)
        if rows is not None:
            self._save_rows(instance, rows)
        return instance

    def _save_rows(self, routine, rows):
        existing = {row.pk: row for row in routine.exercises.all()}
        kept = []
        for order, values in enumerate(rows):
            values = dict(values)
            pk = values.pop("id", None)
            if pk is not None:
                if pk not in existing:
                    raise NotFound("Ese elemento no existe.")
                item = existing[pk]
                for field, value in values.items():
                    setattr(item, field, value)
                item.order = order
                item.save()
            else:
                values.setdefault("rest_seconds", values["exercise"].default_rest)
                item = RoutineExercise.objects.create(routine=routine, order=order, **values)
            kept.append(item.pk)
        routine.exercises.exclude(pk__in=kept).delete()


class RoutineListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Routine
        fields = ("id", "name", "description", "source", "created_at", "exercise_count")


class ScheduleEntrySerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)
    routine_name = serializers.CharField(source="routine.name", read_only=True, default=None)
    is_rest_day = serializers.BooleanField(read_only=True)

    class Meta:
        model = ScheduleEntry
        fields = ("id", "program", "weekday", "weekday_label", "routine", "routine_name",
                  "is_rest_day")
        read_only_fields = ("program", "weekday")

    def validate_routine(self, value):
        if value and value.user != self.context["request"].user:
            raise serializers.ValidationError("Esa rutina no es tuya.")
        return value


class ProgramSerializer(serializers.ModelSerializer):
    schedule = ScheduleEntrySerializer(many=True, read_only=True)
    source_label = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = Program
        fields = ("id", "name", "description", "is_active", "source", "source_label",
                  "created_at", "schedule")
        read_only_fields = ("source", "created_at")


class ProgramListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ("id", "name", "description", "is_active", "source", "created_at")


class SetLogSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = SetLog
        fields = ("id", "session", "exercise", "exercise_name", "set_number", "weight_kg",
                  "reps", "rpe", "is_warmup", "completed")

    def validate_session(self, value):
        if value.user != self.context["request"].user:
            raise serializers.ValidationError("Esa sesión no es tuya.")
        return value

    def validate_exercise(self, value):
        if not Exercise.objects.visible_to(self.context["request"].user).filter(
            pk=value.pk
        ).exists():
            raise serializers.ValidationError("Ese ejercicio no existe.")
        return value


class WorkoutSessionSerializer(serializers.ModelSerializer):
    sets = SetLogSerializer(many=True, read_only=True)
    set_count = serializers.IntegerField(read_only=True)
    routine_name = serializers.CharField(
        source="routine.name", read_only=True, default=None, allow_null=True
    )
    duracion_minutos = serializers.SerializerMethodField()
    tonelaje_kg = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ("id", "date", "routine", "routine_name", "started_at", "finished_at",
                  "notes", "sets", "set_count", "duracion_minutos", "tonelaje_kg")
        read_only_fields = ("started_at", "finished_at")
        extra_kwargs = {
            "date": {"required": False},
        }

    def get_duracion_minutos(self, obj):
        if not obj.started_at or not obj.finished_at:
            return None
        return round((obj.finished_at - obj.started_at).total_seconds() / 60)

    def get_tonelaje_kg(self, obj):
        return tonelaje_simple(obj.sets.all())

    def validate_routine(self, value):
        if value and value.user != self.context["request"].user:
            raise serializers.ValidationError("Esa rutina no es tuya.")
        return value


class BodyWeightEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyWeightEntry
        fields = ("id", "date", "weight_kg", "body_fat_pct", "notes", "created_at")

    def validate_date(self, value):
        user = self.context["request"].user
        existente = BodyWeightEntry.objects.filter(user=user, date=value)
        if self.instance:
            existente = existente.exclude(pk=self.instance.pk)
        if existente.exists():
            raise serializers.ValidationError(
                "Ya tienes un registro para ese día. Edítalo en lugar de crear otro."
            )
        return value


class NotificationSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "kind", "kind_label", "severity", "title", "body",
                  "payload", "is_read", "emailed_at", "created_at")
        read_only_fields = ("kind", "severity", "title", "body", "payload", "emailed_at",
                            "created_at")


class MetricSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(read_only=True)
    visible = serializers.SerializerMethodField()

    class Meta:
        model = Metric
        fields = ("key", "label", "description", "unit", "category", "category_label", "chart",
                  "visible")

    def get_visible(self, obj) -> bool:
        return obj.key in self.context.get("visibles", set())


class ComputedMetricSerializer(serializers.Serializer):
    key = serializers.CharField(source="metric.key")
    label = serializers.CharField(source="metric.label")
    description = serializers.CharField(source="metric.description")
    unit = serializers.CharField(source="metric.unit")
    category = serializers.CharField(source="metric.category")
    category_label = serializers.CharField(source="metric.category_label")
    chart = serializers.CharField(source="metric.chart")
    value = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    rows = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    coverage_pct = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    has_no_data = serializers.BooleanField(read_only=True)
    is_reliable = serializers.BooleanField(read_only=True)
    empty_hint = serializers.CharField(read_only=True)
    needs = serializers.ListField(child=serializers.CharField(), read_only=True)

    def get_coverage_pct(self, obj):
        return obj.result.coverage_pct

    def get_value(self, obj):
        return obj.result.value

    def get_series(self, obj):
        return obj.result.series

    def get_columns(self, obj):
        return obj.result.columns

    def get_rows(self, obj):
        return obj.result.rows

    def get_coverage(self, obj):
        return obj.result.coverage

    def get_notes(self, obj):
        return obj.result.notes


class ProfileSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)

    class Meta:
        from apps.accounts.models import User

        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "goal", "experience_level", "sex", "birth_date", "height_cm", "age",
            "target_weight_kg", "weekly_weight_change_target_kg",
            "available_days_per_week", "available_equipment", "injuries_notes",
        )
        read_only_fields = ("id", "username")
