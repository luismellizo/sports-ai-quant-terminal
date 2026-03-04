<div align="center">
  <img src="https://img.shields.io/badge/Status-Activo-success" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Next.js-14+-black" alt="Next.js 14+" />
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="Licencia MIT" />

  <h1>⚽ Sports AI: Quant Terminal</h1>
  
  <p>
    <strong>Un sistema avanzado multi-agente de predicción deportiva inspirado en terminales cuantitativas de fondos de inversión.</strong><br>
    Analiza partidos de fútbol, calcula ventajas en el mercado y ofrece recomendaciones de valor (Value Betting) potenciado por Inteligencia Artificial y simulaciones de Monte Carlo.
  </p>
</div>

<hr />

## 🚀 Características Principales

Sports AI no es un simple bot; es una **arquitectura compleja de 13 agentes especializados** trabajando en simultáneo:

- 🧠 **Cerebro NLP:** Entiende lenguaje natural (ej: *"¿Quién gana entre el Madrid y el Barça mañana?"*).
- 📊 **Datos en Tiempo Real:** Se conecta a API-Football para estadístias, H2H, lesiones y alineaciones proyectadas.
- 📈 **Rating ELO Global:** Sistema matemático estilo ajedrez calibrado para 34 ligas mundiales (incluye LATAM y europeas).
- 🎲 **Simulación Monte Carlo:** Ejecuta rápidamente 10,000 partidos virtuales para encontrar la distribución real de probabilidad usando modelos de Poisson ajustados.
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

El proyecto está dividido en dos partes: el **Backend** (Python/FastAPI/LangChain) y el **Frontend** (Next.js/React). 

Sigue estos pasos para clonar y operar tu propia terminal:

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/sports-ai-terminal.git
cd sports-ai-terminal
```

### 2. Configurar Credenciales (APIs y LLMs)
Necesitarás dos llaves fundamentales:
1. **API-Football Key:** Obtenla gratis en [api-football.com](https://www.api-football.com/).
2. **OpenAI / Azure OpenAI Key:** Para el procesamiento lógico de los agentes.

Copia el archivo de entorno base y agrega tus llaves:
```bash
cp .env.example .env
```
Abre el archivo `.env` en tu editor y rellena los datos ocultos:
```ini
API_FOOTBALL_KEY=tu_llave_aqui_1234
AZURE_OPENAI_API_KEY=tu_llave_azure_o_openai
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
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
> - Backend: `cd backend && uvicorn app.main:app --reload`
> - Frontend: `cd frontend && npm run dev`

<br/>

## 💡 Cómo usar la Terminal

1. Abre `http://localhost:3000` en tu navegador.
2. En la consola verde pálida que parpadea abajo, escribe en lenguaje natural. 
   - *Ejemplos:*
     - `analiza barcelona vs real madrid`
     - `dame el pronostico para millonarios contra santa fe`
     - `quien tiene más edge mañana: arsenal o chelsea?`
3. Observa cómo los 13 agentes de la red cobran vida en el panel izquierdo procesando datos concurrentemente.
4. En cuestión de 5-10 segundos, recibe la matriz total matemática y la **Recomendación de Apuesta**.

<br/>

## 🏗️ Arquitectura del Sistema

El flujo de trabajo `(Workflow)` dentro del orquestador es el siguiente:
1. **NLP Parse:** Entrada de usuario -> Objeto de Partido (Equipos, Liga).
2. **Data Fetching (Parallel):** Se disparan simultáneamente los agentes de `Historia`, `Alineaciones`, `Estado de Forma` y `Cuotas Actuales`.
3. **Feature Engineering:** Se estandarizan las métricas usando un modelo rating ELO y un Poisson Agent que calcula los Goles Esperados ($\lambda$).
4. **Machine Learning / Simulación:** Se ejecuta un `MonteCarloAgent` (10k iteraciones de resultados).
5. **Decisión:** Un `MarketEdgeAgent` cruza la simulación vs las cuotas reales. 
6. **Risk Management:** Se empaqueta en una recomendación final con una confianza (1 a 10) y tamaño de unidad de apuesta.

<br/>

## 👨‍💻 Contribución

Este proyecto está abierto para la comunidad Quant y entusiastas de los datos deportivos. Si tienes sugerencias para mejorar los modelos estadísticos (como integraciones xG avanzadas, clima, o árbitros), siéntete libre de hacer un Fork y un Pull Request.

---
📝 *Diseñado y construido para el análisis de valor real. ¡Juega de forma responsable!*
