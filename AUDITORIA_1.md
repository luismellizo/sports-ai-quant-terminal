

# AUDITORÍA 1: Análisis de Datos Históricos del Sistema

## Tu Premisa: ¿Estás en lo Correcto?

**SÍ, tienes razón.** El sistema debería obtener TODOS los datos históricos de la API cuando el usuario pide una predicción. **Sin embargo, hay un problema crítico: Statpal (la API primaria) NO proporciona xG ni métricas avanzadas según lo implementado en el código.**

---

## DESCUBRIMIENTO CRÍTICO: El Sistema Tiene ML Pero No Lo Usa

**Existe `TrainingService` (training_service.py)** con modelos entrenados (Logistic Regression, Random Forest, XGBoost) pero:

1. **Entrena con DATOS SINTÉTICOS**, no con datos reales de la API
2. **El modelo NO se usa en producción** - el pipeline actual no llama a `TrainingService`
3. **FeatureAgent genera features** incluyendo `xg_difference` pero el valor es un PROXY, no xG real

```python
# training_service.py - LÍNEA 61-64
def _generate_synthetic_data(self, n_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for initial model setup.
    In production, this would be replaced with real historical match data.
    """
```

---

## Lo que SÍ obtiene Statpal (según el código):

---

## Estado Actual: Lo que el Sistema OBTIENE de la API

### HistoryAgent (Agente 4)
```python
home_last_20 = await api.get_fixtures(team_id=home_id, last=20)  # 20 partidos
away_last_20 = await api.get_fixtures(team_id=away_id, last=20)  # 20 partidos
h2h = await api.get_h2h(home_id, away_id, last=20)              # H2H hasta 20
```

### ContextAgent (Agente 3)
```python
home_season_stats = await api.get_team_statistics(home_id, league_id, season)
away_season_stats = await api.get_team_statistics(away_id, league_id, season)
raw_standings = await api.get_standings(league_id, season)
```

### LineupAgent (Agente 5)
```python
lineups = await api.get_lineups(fixture_id)
injuries_home = await api.get_injuries(team_id=home_id)
injuries_away = await api.get_injuries(team_id=away_id)
```

### OddsAgent (Agente 8)
```python
raw_odds = await api.get_odds(fixture_id=fixture_id)
```

---

## Lo que FALTA u OCCUPAR MEJOR

### 1. **xG (Expected Goals) Real**
El sistema NO obtiene xG de la API. En su lugar calcula un **PROXY rudimentario**:

```python
# feature_engineering.py - LO QUE HACE ACTUALMENTE
attack_rating = avg_scored * 35  # NO es xG real
defense_rating = 100 - avg_conceded * 30  # NO es xG real
```

**Problema:** `avg_scored` son solo goles anotados, no xG. Un equipo puede tener 10 disparos y meter 1, mientras otro tuvo 3 y metió 1. El xG captura la calidad de las oportunidades.

**Solución:** Statpal y API-Football tienen datos xG. El sistema debería pedirlos.

---

### 2. **Métricas Avanzadas No Solicitadas**
La API puede proporcionar pero el sistema NO pide:
- Posesión %
- Tiros (totales, a puerta)
- Corners
- Tarjetas (amarillas, rojas)
- Pases totales, precisión de pases
- Jugadas de gol peligrosas
- Datos de Expected Goals (xG, xA)

Estos datos aparecen en la respuesta de `get_team_statistics()` pero no se extraen ni usan.

---

### 3. **H2H Limitado a 20 Partidos**
```python
h2h = await api.get_h2h(home_id, away_id, last=20)  # Solo 20
```
Para rivales como Barcelona vs Real Madrid, 20 partidos puede no cubrir toda la historia relevante. El H2H completo sería más valioso.

---

### 4. **Datos de Partido Detallados**
El sistema solo extrae:
```python
goals_home, goals_away  # Solo marcador
```

Pero NO extrae de la API:
- Quién generó las ocasiones
- Momento de los goles (minutos)
- Estadísticas detalladas del partido (posesión, disparos, corners)

---

### 5. **Temporada Completa vs Últimos 20 Partidos**
`get_fixtures(last=20)` solo da los últimos 20 partidos jugados, sin importar la temporada. Para un análisis de forma actual, esto está bien. Pero para estadísticas de temporada completa, `get_team_statistics()` debería dar la información completa.

---

## ¿Qué Datos Tiene la API Statpal/API-Football?

Revisando `api_football_client.py`, la API SÍ proporciona datos ricos:

### get_team_statistics()
Retorna estructura completa con:
- `fixtures`: wins/draws/losses (total, home, away)
- `goals`: for/against (total, home, away)
- `lineups`: formaciones preferidas

### get_fixtures() - Detalles por partido
Retorna:
- `goals`: marcadores
- `score`: HT/FT
- `fixture`: fecha, status
- `league`: info de liga

### LO QUE NO SE ESTÁ USANDO de get_fixtures():
- Estadísticas detalladas del partido (si la API las proporciona)

---

## Resumen: Tu Argumento es Válido

| Tu Propuesta | Estado Actual | Gap |
|-------------|---------------|-----|
| API debe dar historial completo de ambos equipos | SÍ obtiene 20 partidos | Cantidad limitada |
| API debe dar H2H completo | SÍ obtiene H2H (20 max) | Podría ser más |
| API debe dar stats de temporada | SÍ obtiene team_statistics | Pero no extrae todos los campos |
| API debe dar alineaciones | SÍ, si hay fixture | Depende de si está publicado |
| API debe dar lesiones | SÍ obtiene injuries | Busca por team, no por fixture |
| **xG real de la API** | **NO** | Solo usa goles como proxy |
| **Métricas avanzadas (posesión, tiros)** | **NO** | No se piden ni extraen |

---

---

## Lo que NO tiene Statpal Implementado

1. **Match Statistics** (posesión, disparos, corners, etc.) - NO HAY ENDPOINT
2. **xG (Expected Goals)** - NO ESTÁ EN NINGÚN ENDPOINT
3. **Player Statistics** detalladas - NO SE IMPLEMENTA
4. **Fixture Statistics** por partido - NO EXISTE

El sistema solo usa:
- `league_stats` (estadísticas de liga por equipo: wins/draws/losses/goals)
- Marcadores de partidos (no stats detalladas)

---

## API-Football SÍ Tiene Statistics (Según Cobertura)

La cobertura de API-Football incluye **"Statistics"** explícitamente:
- Fixtures
- Players
- Standings
- Events
- Lineups
- **Statistics**
- Players
- Predictions
- Odds
- Top Scorers

**Esto significa que API-Football SÍ proporciona estadísticas detalladas**, pero el sistema está usando Statpal como API primaria.

---

## Resumen: Tu Argumento Es Válido Pero Con Matices

| Tu Propuesta | API Actual | Gap |
|-------------|------------|-----|
| API debe dar historial completo | **SÍ** (20 partidos) | Cantidad suficiente |
| API debe dar H2H completo | **SÍ** (20 max) | Suficiente |
| API debe dar stats de temporada | **SÍ** | Campos limitados |
| API debe dar alineaciones | **SÍ** | Depende de publicación |
| API debe dar lesiones | **SÍ** | Busca por equipo, no por partido |
| **API debe dar xG real** | **NO** (Statpal no lo tiene implementado) | CRÍTICO |
| **API debe dar métricas avanzadas** | **NO** (Statpal no lo provee) | Posesión, disparos, corners |
| **Modelo ML con datos reales** | **NO** (usa datos sintéticos) | CRÍTICO |

---

## Recomendación

**Tu enfoque es correcto.** El sistema debe obtener más datos de la API. Las prioridades serían:

### 1. Cambiar a API-Football o Agregar Endpoints Statpal
- Statpal no parece proporcionar xG ni estadísticas detalladas
- API-Football SÍ tiene "Statistics" en su cobertura
- Evaluar si Statpal tiene endpoint de statistics no implementado

### 2. Implementar TrainingService con Datos Reales
- Actualmente usa datos sintéticos
- Debería usar `api.get_fixtures()` con stats detalladas para entrenar
- Necesitaríamos que la API proporcione las features

### 3. Validar Capabilities Reales de Statpal
- ¿Statpal proporciona xG en algún endpoint no usado?
- ¿Proporciona posesión, disparos, corners en `get_fixtures()`?
- ¿Cuántos partidos históricos puede devolver por llamada?

---

## Próximos Pasos Sugeridos

1. **Hacer una llamada de prueba** a Statpal para ver qué campos trae `get_fixtures()` con statistics
2. **Verificar si existe** `{sport}/fixtures/{id}/statistics` en Statpal
3. **Comparar con API-Football** endpoint: `https://v3.football.api-sports.io/statistics?fixture={id}`
4. **Decidir** si migrar a API-Football o implementar endpoints adicionales en Statpal adapter

Estas respuestas determinarán cuánto del historial podemos obtener directamente de la API vs cuánto tendríamos que calcular.
