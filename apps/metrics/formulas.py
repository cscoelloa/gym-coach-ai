from datetime import date

MAX_REPS_FOR_E1RM = 12


def epley_1rm(weight_kg: float | None, reps: int | None) -> float | None:
    if weight_kg is None or reps is None:
        return None
    if weight_kg <= 0 or reps < 1 or reps > MAX_REPS_FOR_E1RM:
        return None
    if reps == 1:
        return float(weight_kg)
    return float(weight_kg) * (1 + reps / 30)


def linear_slope(points: list[tuple[float, float]]) -> float | None:
    if len(points) < 2:
        return None

    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n

    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        return None

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in points)
    return numerator / denominator


def moving_average(values: list[float], window: int) -> list[float | None]:
    if window < 1:
        raise ValueError("La ventana debe ser de al menos 1.")

    out: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            out.append(None)
        else:
            chunk = values[index + 1 - window : index + 1]
            out.append(sum(chunk) / window)
    return out


def week_key(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def week_label(key: str) -> str:
    return f"sem. {key.split('-W')[1]}"


def safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def coverage_of(available: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return available / total
