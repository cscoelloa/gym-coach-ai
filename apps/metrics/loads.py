from decimal import Decimal

DIRECT_CONTRIBUTION = 1.0
INDIRECT_CONTRIBUTION = 0.5

EFFECTIVE_RPE = Decimal("7")


def is_working_set(set_log) -> bool:
    return (
        set_log.completed
        and not set_log.is_warmup
        and not set_log.exercise.is_cardio
    )


def is_effective_set(set_log) -> bool:
    if not is_working_set(set_log):
        return False
    if set_log.rpe is None:
        return True
    return set_log.rpe >= EFFECTIVE_RPE


def effective_load(set_log, bodyweight_kg: Decimal | None) -> Decimal | None:
    if set_log.exercise.is_bodyweight:
        if bodyweight_kg is None:
            return None
        return bodyweight_kg + (set_log.weight_kg or Decimal("0"))
    return set_log.weight_kg


def total_work(set_log, bodyweight_kg: Decimal | None) -> Decimal | None:
    load = effective_load(set_log, bodyweight_kg)
    if load is None:
        return None
    return load * 2 if set_log.exercise.is_unilateral else load


def muscle_contributions(exercise) -> dict[str, float]:
    contributions: dict[str, float] = {}

    if exercise.target_muscle_id:
        contributions[exercise.target_muscle.slug] = DIRECT_CONTRIBUTION

    for muscle in exercise.secondary_muscles.all():
        contributions.setdefault(muscle.slug, INDIRECT_CONTRIBUTION)

    return contributions


def muscle_names(exercise) -> dict[str, str]:
    names = {}
    if exercise.target_muscle_id:
        names[exercise.target_muscle.slug] = exercise.target_muscle.name
    for muscle in exercise.secondary_muscles.all():
        names.setdefault(muscle.slug, muscle.name)
    return names
