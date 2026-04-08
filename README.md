<div align="center">
  <img src="https://img.shields.io/badge/Status-Activo-success" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Next.js-14+-black" alt="Next.js 14+" />
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="Licencia MIT" />

  <h1>⚽ Sports AI: Quant Terminal</h1>
  
  <p>
    <strong>Un sistema multi-agente de predicción deportiva inspirado en terminales cuantitativas de fondos de inversión.</strong><br>
    Analiza partidos de fútbol, calcula ventajas en el mercado y ofrece recomendaciones de valor (Value Betting) con IA, reglas cuantitativas y simulaciones de Monte Carlo.
  </p>
</div>

<hr />

## 🚀 Características Principales

Sports AI no es un simple bot; es una **arquitectura modular de 15 agentes especializados** ejecutados por etapas, con paralelismo real en los tramos independientes:

- 🧠 **Cerebro NLP:** Entiende lenguaje natural (ej: *"¿Quién gana entre el Madrid y el Barça mañana?"*).
- 📊 **Datos en Tiempo Real:** Usa Statpal como fuente primaria y conserva compatibilidad con API-Football como respaldo para datos históricos y cobertura legacy.
- 📈 **Rating ELO Global:** Sistema matemático estilo ajedrez calibrado para 34 ligas mundiales (incluye LATAM y europeas).
- 🎲 **Simulación Monte Carlo:** Ejecuta 50,000 partidos virtuales para encontrar la distribución real de probabilidad usando modelos de Poisson ajustados.
- 📉 **Detección de Valor (Market Edge):** Compara las cuotas en vivo de las casas de apuestas vs. nuestras probabilidades matemáticas para detectar dónde está el error del mercado.
- 💬 **Análisis de Sentimiento:** Agente LLM especializado que rastrea el contexto mediático, motivación y urgencia competitiva.
- 🛡️ **Recomendación de Stake:** Sugiere cuánto apostar basado en el ratio Riesgo/Confianza usando criterio de Kelly fraccional.

<br/>

## 🎨 Interfaz Gráfica (Quant UI)

La aplicación cuenta con una terminal front-end desarrollada en **React / Next.js** diseñada bajo las filosofías de las terminales de Bloomberg:
- Panel visual de matriz de agentes con animaciones de latido (`pulse-glow`) mientras operan.
- Dashboard de métricas duras (xG, Spread, Edge) tipográficamente impactantes.
- Soporte total para español (i18n nativo en el output) y Dark Mode absoluto.

<br/>

## ⚙️ Instalación y Configuración

El proyecto está dividido en dos partes: el **Backend** (Python/FastAPI) y el **Frontend** (Next.js/React).

Sigue estos pasos para clonar y operar tu propia terminal:

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/sports-ai-terminal.git
cd sports-ai-terminal
```

### 2. Configurar Credenciales (APIs y LLMs)
Necesitarás dos llaves fundamentales:
1. **Statpal Access Key:** Obtenla en [statpal.io](https://statpal.io).
2. **DeepSeek API Key:** Para el procesamiento lógico de los agentes.

Copia el archivo de entorno base y agrega tus llaves:
```bash
cp .env.example .env
```
Abre el archivo `.env` en tu editor y rellena los datos ocultos:
```ini
STATPAL_ACCESS_KEY=tu_llave_statpal_aqui
DEEPSEEK_API_KEY=tu_llave_deepseek
```
> **Nota de Seguridad:** El archivo `.env` ya está incluido en el `.gitignore`. ¡Nunca subas tus llaves a GitHub!

### 3. Entorno de Python (Backend)
Se recomienda encarecidamente usar un entorno virtual (`venv`):

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

pip install -r requirements.txt
cd ..
```

### 4. Entorno de Node (Frontend)
```bash
cd frontend
npm install
cd ..
```

<br/>

## ▶️ Ejecución Rápida

Hemos incluido un script maestro (`start.sh`) que levanta de forma segura tanto el backend como el frontend, matando procesos zombis previos si los hubiera:

```bash
chmod +x start.sh
./start.sh
```

- **Frontend (UI Terminal):** `http://localhost:3000`
- **Backend (FastAPI Docs):** `http://localhost:8000/docs`

> *Si prefieres correrlos por separado:*
> - Backend: `python3 -m uvicorn backend.main:app --reload`
> - Frontend: `cd frontend && npm run dev`

<br/>

## 💡 Cómo usar la Terminal

1. Abre `http://localhost:3000` en tu navegador.
2. En la consola verde pálida que parpadea abajo, escribe en lenguaje natural.
   - *Ejemplos:*
     - `analiza barcelona vs real madrid`
     - `dame el pronostico para millonarios contra santa fe`
     - `quien tiene más edge mañana: arsenal o chelsea?`
3. Observa cómo los 15 agentes se activan por etapas y se ejecutan en paralelo cuando el grafo lo permite.
4. En cuestión de pocos segundos, recibe la matriz total matemática y la **Recomendación de Apuesta**.

<br/>

## 🏗️ Arquitectura del Sistema

El flujo de trabajo dentro del orquestador es el siguiente:
1. **Parseo y resolución:** NLP -> Fixture Resolver -> Contexto.
2. **Datos en paralelo:** `History`, `Lineup` y `Odds` se ejecutan como fan-out independiente.
3. **Análisis cuantitativo:** `Sentiment`, `Elo` y `Poisson` refinan la lectura del partido.
4. **Ensamblado de features:** `FeatureAgent` prepara las variables para los modelos.
5. **Predicción y simulación:** `MLAgent` y `MonteCarloAgent` producen probabilidades y distribución de resultados.
6. **Edge y riesgo:** `MarketEdgeAgent` y `RiskAgent` convierten señales en recomendación accionable.
7. **Síntesis final:** `SynthesisAgent` resume el análisis ejecutivo.

### Estructura actual relevante
- Agentes en `backend/agents/<nombre>/`
- Orquestación en `backend/agents/core/`
- Utilidades compartidas en `backend/agents/shared/`
- Artefactos de modelos en `artifacts/models/`
- Salud del servicio en `/api/health`, `/api/health/live` y `/api/health/ready`

<br/>

## 👨‍💻 Contribución

Este proyecto está abierto para la comunidad Quant y entusiastas de los datos deportivos. Si tienes sugerencias para mejorar los modelos estadísticos (como integraciones xG avanzadas, clima, o árbitros), siéntete libre de hacer un Fork y un Pull Request.

---
📝 *Diseñado y construido para el análisis de valor real. ¡Juega de forma responsable!*
