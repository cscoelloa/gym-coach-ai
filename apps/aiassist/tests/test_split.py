import pytest
from django.contrib.auth import get_user_model

from apps.aiassist.services.split import (
    DiaDelReparto,
    RepartoInvalido,
    conflictos_de_recuperacion,
    dias_sugeridos,
    format_split,
    musculos_del_reparto,
    parse_split,
)
from apps.workouts.models import Exercise, MuscleGroup

pytestmark = pytest.mark.django_db

User = get_user_model()

MUSCULOS = [
    ("pectorals", "Pectorales", "chest"),
    ("triceps", "Tríceps", "upper arms"),
    ("lats", "Dorsales", "back"),
    ("quads", "Cuádriceps", "upper legs"),
    ("abs", "Abdominales", "waist"),
]


@pytest.fixture
def user():
    return User.objects.create_user("atleta", password="Contrasena-Larga-1")


@pytest.fixture(autouse=True)
def catalogo():
    for slug, nombre, zona in MUSCULOS:
        musculo = MuscleGroup.objects.create(slug=slug, name=nombre)
        for numero in range(4):
            Exercise.objects.create(
                external_id=f"{slug}{numero}", name=f"{nombre} {numero}", slug=f"{slug}-{numero}",
                body_part=zona, equipment="barbell", target_muscle=musculo, is_global=True,
            )


def dia(weekday, musculos, *, enfasis=None, ejercicios=6) -> dict:
    return {
        "weekday": weekday,
        "muscles": musculos,
        "emphasis": enfasis,
        "exercises": ejercicios,
    }


class TestParseo:
    def test_un_reparto_corriente(self, user):
        reparto = parse_split(
            [
                dia(0, ["pectorals", "triceps"], enfasis="pectorals", ejercicios=8),
                dia(2, ["quads"]),
            ],
            user=user,
        )

        assert [d.weekday for d in reparto] == [0, 2]
        assert reparto[0].muscles == ("pectorals", "triceps")
        assert reparto[0].emphasis == "pectorals"
        assert reparto[0].exercises == 8

    def test_los_dias_sin_musculos_son_descanso_y_no_viajan(self, user):
        reparto = parse_split([dia(0, ["pectorals"]), dia(1, [])], user=user)

        assert [d.weekday for d in reparto] == [0]

    def test_llegan_desordenados_y_salen_ordenados(self, user):
        reparto = parse_split([dia(4, ["quads"]), dia(0, ["pectorals"])], user=user)

        assert [d.weekday for d in reparto] == [0, 4]

    def test_sin_ningun_dia_de_entrenamiento(self, user):
        with pytest.raises(RepartoInvalido, match="al menos un día"):
            parse_split([dia(0, [])], user=user)

    def test_un_dia_repetido(self, user):
        with pytest.raises(RepartoInvalido, match="Lunes aparece dos veces"):
            parse_split([dia(0, ["pectorals"]), dia(0, ["lats"])], user=user)

    def test_un_dia_que_no_existe(self, user):
        with pytest.raises(RepartoInvalido, match="no es un día"):
            parse_split([dia(9, ["pectorals"])], user=user)

    def test_un_musculo_que_no_esta_en_el_catalogo(self, user):
        with pytest.raises(RepartoInvalido, match="no se puede entrenar"):
            parse_split([dia(0, ["inventado"])], user=user)

    def test_un_musculo_que_no_se_puede_entrenar_con_su_material(self, user):
        user.available_equipment = ["cable"]
        user.save()

        with pytest.raises(RepartoInvalido, match="con tu equipamiento"):
            parse_split([dia(0, ["pectorals"])], user=user)

    def test_demasiados_musculos_en_un_dia(self, user):
        with pytest.raises(RepartoInvalido, match="como mucho"):
            parse_split(
                [dia(0, ["pectorals", "triceps", "lats", "quads", "abs", "pectorals2"])],
                user=user,
            )

    def test_el_enfasis_tiene_que_estar_entre_los_musculos_del_dia(self, user):
        with pytest.raises(RepartoInvalido, match="no está entre los músculos"):
            parse_split([dia(0, ["pectorals"], enfasis="quads")], user=user)

    def test_los_ejercicios_tienen_tope(self, user):
        with pytest.raises(RepartoInvalido, match="van de 3 a 10"):
            parse_split([dia(0, ["pectorals"], ejercicios=25)], user=user)

    def test_no_caben_menos_ejercicios_que_musculos(self, user):
        with pytest.raises(RepartoInvalido, match="se quedaría sin ninguno"):
            parse_split(
                [dia(0, ["pectorals", "triceps", "lats", "quads"], ejercicios=3)], user=user
            )

    def test_los_musculos_repetidos_en_un_dia_se_colapsan(self, user):
        reparto = parse_split([dia(0, ["pectorals", "pectorals", "lats"])], user=user)

        assert reparto[0].muscles == ("pectorals", "lats")


class TestRecuperacion:
    def test_dos_dias_seguidos_con_el_mismo_musculo(self):
        conflictos = conflictos_de_recuperacion([
            DiaDelReparto(0, ("pectorals", "triceps"), None, 6),
            DiaDelReparto(1, ("pectorals",), None, 6),
        ])

        assert len(conflictos) == 1
        assert "Lunes y Martes repiten Pectorales" in conflictos[0]
        assert "48 h" in conflictos[0]

    def test_dias_alternos_no_son_conflicto(self):
        assert not conflictos_de_recuperacion([
            DiaDelReparto(0, ("pectorals",), None, 6),
            DiaDelReparto(2, ("pectorals",), None, 6),
        ])

    def test_domingo_y_lunes_tambien_cuentan(self):
        conflictos = conflictos_de_recuperacion([
            DiaDelReparto(0, ("quads",), None, 6),
            DiaDelReparto(6, ("quads",), None, 6),
        ])

        assert conflictos and "Domingo y Lunes" in conflictos[0]

    def test_abdominales_gemelos_y_antebrazos_aguantan_dias_seguidos(self):
        assert not conflictos_de_recuperacion([
            DiaDelReparto(0, ("abs",), None, 6),
            DiaDelReparto(1, ("abs",), None, 6),
        ])


class TestFormato:
    def test_salen_los_siete_dias_y_el_descanso_se_nombra(self):
        texto = format_split([DiaDelReparto(0, ("pectorals",), "pectorals", 8)])

        assert "Lunes: Pectorales — exactamente 8 ejercicios, con énfasis en Pectorales" in texto
        assert texto.count("DESCANSO") == 6

    def test_los_musculos_del_reparto_salen_sin_repetir(self):
        todos, enfasis = musculos_del_reparto([
            DiaDelReparto(0, ("pectorals", "triceps"), "pectorals", 6),
            DiaDelReparto(2, ("pectorals", "quads"), "quads", 6),
        ])

        assert todos == ["pectorals", "triceps", "quads"]
        assert enfasis == ["pectorals", "quads"]


class TestDiasSugeridos:
    @pytest.mark.parametrize(
        "cuantos,esperado",
        [(3, [0, 2, 4]), (5, [0, 1, 2, 4, 5]), (7, list(range(7)))],
    )
    def test_el_descanso_queda_intercalado(self, cuantos, esperado):
        assert dias_sugeridos(cuantos) == esperado

    def test_un_valor_imposible_no_revienta(self):
        assert dias_sugeridos(None) and dias_sugeridos(99) == list(range(7))
