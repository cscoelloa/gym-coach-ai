# Visión

## Qué es

Una aplicación web de gimnasio donde una persona planifica su semana de entrenamiento, registra lo
que realmente levanta y deja que una IA le diga cuándo ha dejado de progresar.

## El problema

Quien entrena en serio acaba llevando su rutina en una libreta o una hoja de cálculo. Eso sirve para
*anotar*, pero no para *detectar*. Los dos fallos que nadie ve a tiempo:

1. **Estancamiento silencioso.** Llevas nueve semanas haciendo press de banca con el mismo peso y las
   mismas repeticiones. No hay ningún momento en que suene una alarma; simplemente un día te das
   cuenta de que llevas dos meses igual.
2. **Deriva respecto al objetivo.** Dices que estás en volumen, pero llevas tres semanas perdiendo
   200 g cada una. La báscula te da un número suelto cada día; nadie te dice la tendencia.

Las dos cosas son detectables con datos que el usuario ya está anotando. Lo que falta es que alguien
los mire.

## Qué hace la aplicación

- **Rutinas de lunes a domingo** con ejercicios, series, repeticiones, RPE y tiempo de descanso.
  Se pueden crear a mano o pedirle una a la IA.
- **Registro de entrenamiento**: peso levantado, repeticiones y RPE por serie, con el GIF del
  ejercicio y el temporizador de descanso a la vista.
- **Registro de peso corporal** con gráfico de tendencia.
- **Generación de rutinas con IA**, fundamentada en literatura de hipertrofia mediante RAG
  (el admin sube los libros; la IA los consulta).
- **Análisis de progreso**: detecta ejercicios estancados, patrones de falta de progresión y
  problemas de adherencia; **notifica al usuario** y propone una rutina correctiva.
- **Análisis de peso**: compara cada registro nuevo con la tendencia previa y avisa si el ritmo real
  no cuadra con el objetivo declarado.

## Para quién

Personas que ya entrenan con cierta constancia y quieren progresar de forma medida, no principiantes
absolutos buscando una rutina genérica. El valor está en el historial: la aplicación es más útil
cuanto más tiempo lleva usándose.

## Principio de diseño

**La aritmética la hace el código; la IA interpreta.**

Los cálculos de 1RM estimado, volumen semanal por grupo muscular, pendientes de progresión y medias
móviles de peso viven en `apps/workouts/metrics.py` y están cubiertos por tests. El LLM recibe esos
números ya masticados y hace lo que sí sabe hacer: leerlos en contexto, cruzarlos con la literatura y
redactar una recomendación.

Pedirle a un modelo que sume series es regalar una fuente de error que nadie va a detectar en
revisión. Un número mal calculado en Python lo caza un test.

## Alcance explícito

**Dentro:** rutinas, registro, peso corporal, IA configurable por el admin, RAG, análisis, notificaciones,
API REST para un futuro cliente móvil.

**Fuera, por ahora:** nutrición y conteo de calorías, funciones sociales, integración con wearables,
pagos.
