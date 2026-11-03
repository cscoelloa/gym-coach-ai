from django.db import models


class BodyPart(models.TextChoices):
    BACK = "back", "Espalda"
    CARDIO = "cardio", "Cardio"
    CHEST = "chest", "Pecho"
    LOWER_ARMS = "lower arms", "Antebrazos"
    LOWER_LEGS = "lower legs", "Pierna inferior"
    NECK = "neck", "Cuello"
    SHOULDERS = "shoulders", "Hombros"
    UPPER_ARMS = "upper arms", "Brazos"
    UPPER_LEGS = "upper legs", "Piernas"
    WAIST = "waist", "Zona media"


class Equipment(models.TextChoices):
    ASSISTED = "assisted", "Asistido"
    BAND = "band", "Banda"
    BARBELL = "barbell", "Barra"
    BODY_WEIGHT = "body weight", "Peso corporal"
    BOSU_BALL = "bosu ball", "Bosu"
    CABLE = "cable", "Polea"
    DUMBBELL = "dumbbell", "Mancuerna"
    ELLIPTICAL = "elliptical machine", "Elíptica"
    EZ_BARBELL = "ez barbell", "Barra Z"
    HAMMER = "hammer", "Máquina Hammer"
    KETTLEBELL = "kettlebell", "Kettlebell"
    LEVERAGE_MACHINE = "leverage machine", "Máquina de palanca"
    MEDICINE_BALL = "medicine ball", "Balón medicinal"
    OLYMPIC_BARBELL = "olympic barbell", "Barra olímpica"
    RESISTANCE_BAND = "resistance band", "Banda de resistencia"
    ROLLER = "roller", "Rodillo"
    ROPE = "rope", "Cuerda"
    SKIERG = "skierg machine", "SkiErg"
    SLED = "sled machine", "Trineo"
    SMITH_MACHINE = "smith machine", "Multipower"
    STABILITY_BALL = "stability ball", "Fitball"
    STATIONARY_BIKE = "stationary bike", "Bicicleta estática"
    STEPMILL = "stepmill machine", "Escaladora"
    TIRE = "tire", "Neumático"
    TRAP_BAR = "trap bar", "Barra hexagonal"
    UPPER_BODY_ERGOMETER = "upper body ergometer", "Ergómetro de brazos"
    WEIGHTED = "weighted", "Con lastre"
    WHEEL_ROLLER = "wheel roller", "Rueda abdominal"


MUSCLE_ALIASES = {
    "abdominals": "abs",
    "core": "abs",
    "lower abs": "abs",
    "latissimus dorsi": "lats",
    "trapezius": "traps",
    "quadriceps": "quads",
    "deltoids": "delts",
    "rear deltoids": "delts",
    "shoulders": "delts",
    "chest": "pectorals",
    "upper chest": "pectorals",
    "soleus": "calves",
    "back": "upper back",
    "inner thighs": "adductors",
    "groin": "adductors",
    "wrist extensors": "forearms",
    "wrist flexors": "forearms",
    "grip muscles": "forearms",
    "wrists": "forearms",
    "hands": "forearms",
}

MUSCLE_ES = {
    "abs": "Abdominales",
    "abductors": "Abductores",
    "adductors": "Aductores",
    "ankle stabilizers": "Estabilizadores del tobillo",
    "ankles": "Tobillos",
    "biceps": "Bíceps",
    "brachialis": "Braquial",
    "calves": "Gemelos",
    "cardiovascular system": "Sistema cardiovascular",
    "delts": "Deltoides",
    "feet": "Pies",
    "forearms": "Antebrazos",
    "glutes": "Glúteos",
    "hamstrings": "Isquiotibiales",
    "hip flexors": "Flexores de cadera",
    "lats": "Dorsales",
    "levator scapulae": "Elevador de la escápula",
    "lower back": "Espalda baja",
    "obliques": "Oblicuos",
    "pectorals": "Pectorales",
    "quads": "Cuádriceps",
    "rhomboids": "Romboides",
    "rotator cuff": "Manguito rotador",
    "serratus anterior": "Serrato anterior",
    "shins": "Tibiales",
    "spine": "Erectores espinales",
    "sternocleidomastoid": "Esternocleidomastoideo",
    "traps": "Trapecio",
    "triceps": "Tríceps",
    "upper back": "Espalda alta",
}


REGION_MUSCLE = {
    "chest-upper-left": "pectorals",
    "chest-lower-left": "pectorals",
    "chest-upper-right": "pectorals",
    "chest-lower-right": "pectorals",
    "abs-upper-left": "abs",
    "abs-lower-left": "abs",
    "abs-upper-right": "abs",
    "abs-lower-right": "abs",
    "obliques-left": "obliques",
    "obliques-right": "obliques",
    "serratus-anterior-left": "serratus-anterior",
    "serratus-anterior-right": "serratus-anterior",
    "traps-upper-left": "traps",
    "traps-upper-right": "traps",
    "traps-lower-left": "traps",
    "traps-lower-right": "traps",
    "traps-mid-left": "upper-back",
    "traps-mid-right": "upper-back",
    "lats-upper-left": "lats",
    "lats-mid-left": "lats",
    "lats-lower-left": "lats",
    "lats-upper-right": "lats",
    "lats-mid-right": "lats",
    "lats-lower-right": "lats",
    "spine": "spine",
    "lower-back-erectors-left": "lower-back",
    "lower-back-erectors-right": "lower-back",
    "lower-back-ql-left": "lower-back",
    "lower-back-ql-right": "lower-back",
    "shoulder-front-left": "delts",
    "shoulder-side-left": "delts",
    "shoulder-front-right": "delts",
    "shoulder-side-right": "delts",
    "deltoid-rear-left": "delts",
    "deltoid-rear-right": "delts",
    "biceps-left": "biceps",
    "biceps-right": "biceps",
    "triceps-long-left": "triceps",
    "triceps-lateral-left": "triceps",
    "triceps-long-right": "triceps",
    "triceps-lateral-right": "triceps",
    "forearm-left": "forearms",
    "forearm-right": "forearms",
    "forearm-flexors-left": "forearms",
    "forearm-extensors-left": "forearms",
    "forearm-flexors-right": "forearms",
    "forearm-extensors-right": "forearms",
    "gluteus-maximus-left": "glutes",
    "gluteus-maximus-right": "glutes",
    "gluteus-medius-left": "abductors",
    "gluteus-medius-right": "abductors",
    "quads-left": "quads",
    "quads-right": "quads",
    "hip-flexor-left": "hip-flexors",
    "hip-flexor-right": "hip-flexors",
    "adductors-left": "adductors",
    "adductors-right": "adductors",
    "hamstrings-medial-left": "hamstrings",
    "hamstrings-lateral-left": "hamstrings",
    "hamstrings-medial-right": "hamstrings",
    "hamstrings-lateral-right": "hamstrings",
    "calves-gastroc-medial-left": "calves",
    "calves-gastroc-lateral-left": "calves",
    "calves-soleus-left": "calves",
    "calves-gastroc-medial-right": "calves",
    "calves-gastroc-lateral-right": "calves",
    "calves-soleus-right": "calves",
    "tibialis-anterior-left": "shins",
    "tibialis-anterior-right": "shins",
    "neck-left": "sternocleidomastoid",
    "neck-right": "sternocleidomastoid",
    "nape": "levator-scapulae",
    "foot-left": "feet",
    "foot-right": "feet",
    "foot-back-left": "feet",
    "foot-back-right": "feet",
}

REGION_INERT = frozenset({
    "head", "face", "head-back",
    "hand-left", "hand-right", "hand-back-left", "hand-back-right",
    "elbow-left", "elbow-right",
    "knee-left", "knee-right", "knee-back-left", "knee-back-right",
})

MUSCLE_WITHOUT_REGION = frozenset({
    "cardiovascular-system",
    "ankles",
    "ankle-stabilizers",
    "rotator-cuff",
    "brachialis",
    "rhomboids",
})


def canonical_muscle(raw: str) -> str:
    key = (raw or "").strip().lower()
    return MUSCLE_ALIASES.get(key, key)


def muscle_slug(canonical: str) -> str:
    return canonical.replace(" ", "-")


MUSCLE_ES_BY_SLUG = {muscle_slug(nombre): etiqueta for nombre, etiqueta in MUSCLE_ES.items()}


def muscle_label(muscle: str) -> str:
    if muscle in MUSCLE_ES:
        return MUSCLE_ES[muscle]
    if muscle in MUSCLE_ES_BY_SLUG:
        return MUSCLE_ES_BY_SLUG[muscle]
    return muscle.replace("-", " ").capitalize()


def muscle_for_region(region_id: str) -> str | None:
    return REGION_MUSCLE.get(region_id)
