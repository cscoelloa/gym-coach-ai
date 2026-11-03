from pydantic import BaseModel, Field


class PlannedExercise(BaseModel):
    external_id: str = Field(
        description="Identificador del ejercicio, tomado literalmente de la lista de candidatos."
    )
    sets: int = Field(description="Número de series de trabajo.")
    reps_min: int = Field(description="Extremo inferior del rango de repeticiones.")
    reps_max: int = Field(description="Extremo superior del rango de repeticiones.")
    rest_seconds: int = Field(description="Descanso entre series, en segundos.")


class PlannedRoutine(BaseModel):
    name: str = Field(
        description="Nombre corto y único de la rutina, por ejemplo «Empuje» o «Pierna»."
    )
    exercises: list[PlannedExercise] = Field(description="Ejercicios de esta rutina, en orden.")


class ScheduledDay(BaseModel):
    weekday: int = Field(description="Día de la semana: 0 es lunes y 6 es domingo.")
    routine_name: str = Field(
        description=(
            "Nombre de una de las rutinas definidas arriba, exactamente igual. "
            "Cadena vacía si ese día es de descanso."
        )
    )


class RoutinePlan(BaseModel):
    name: str = Field(description="Nombre corto del programa, por ejemplo «Empuje/Tirón/Pierna».")
    description: str = Field(description="Para quién es y qué busca, en una o dos frases.")
    routines: list[PlannedRoutine] = Field(
        description="Las rutinas del programa. Normalmente entre 2 y 5, sin repetir nombre."
    )
    schedule: list[ScheduledDay] = Field(
        description="Exactamente siete días, de 0 a 6, indicando qué rutina toca en cada uno."
    )
    rationale: str = Field(
        description="Por qué este programa para esta persona: reparto, volumen y progresión."
    )


class StalledExercise(BaseModel):
    exercise: str = Field(description="Nombre del ejercicio.")
    weeks_stalled: int = Field(description="Semanas sin mejorar.")
    likely_cause: str = Field(description="Causa más probable del estancamiento.")


class ProposedChange(BaseModel):
    target: str = Field(description="Qué cambiar: un ejercicio, un día o el reparto semanal.")
    change: str = Field(description="El cambio concreto a aplicar.")
    reason: str = Field(description="Por qué ese cambio resuelve el problema detectado.")


class ProgressAnalysis(BaseModel):
    summary: str = Field(description="Resumen en dos o tres frases, dirigido a la persona.")
    patterns: list[str] = Field(description="Patrones observados en los datos.")
    stalled: list[StalledExercise] = Field(description="Ejercicios sin progresión.")
    recommendations: list[str] = Field(description="Recomendaciones accionables, en orden.")
    proposed_changes: list[ProposedChange] = Field(description="Cambios concretos a la rutina.")
    data_caveats: list[str] = Field(
        description=(
            "Conclusiones que no se pueden sostener porque faltan datos, según la cobertura "
            "indicada en cada métrica. Lista vacía si no hay ninguna."
        )
    )


class WeightAnalysis(BaseModel):
    trend: str = Field(description="Tendencia: subiendo, bajando o estable.")
    rate_kg_per_week: float | None = Field(
        description="Ritmo real en kg por semana, o null si no hay datos suficientes."
    )
    on_track: bool = Field(description="True si el ritmo encaja con el objetivo de la persona.")
    message: str = Field(description="Qué está pasando, en una o dos frases.")
    recommendation: str = Field(description="Qué ajustar. Vacío si no hace falta cambiar nada.")


class ConnectionTest(BaseModel):
    ok: bool = Field(description="Siempre true.")
    message: str = Field(description="Un saludo corto.")
