"""
Sports AI — News RSS Service
Fetches recent news headlines from Google News RSS for sentiment enrichment.
No API key required. Caches results in Redis to avoid duplicate requests.
"""

import asyncio
import re
import urllib.parse
from typing import List, Optional

import httpx

from backend.utils.cache import get_redis
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Timeout en segundos para la petición HTTP al feed RSS
_RSS_TIMEOUT_SECONDS = 5.0

# TTL del caché en Redis (15 minutos)
_CACHE_TTL_SECONDS = 900

# Máximo de titulares a retornar por equipo
_MAX_HEADLINES = 10

# Base URL de Google News RSS (sin región fija para mayor cobertura)
_GNEWS_RSS_BASE = "https://news.google.com/rss/search"


def _build_rss_url(team_name: str, lang: str = "es") -> str:
    """
    Construye la URL del feed RSS de Google News para un equipo.

    Usa dos queries: una con el nombre del equipo y otra orientada a
    noticias de lesiones/fichajes para maximizar la relevancia.
    """
    region_map = {
        "es": ("es", "ES", "ES:es"),
        "en": ("en", "US", "US:en"),
        "pt": ("pt-419", "MX", "MX:pt-419"),
    }
    hl, gl, ceid = region_map.get(lang, region_map["es"])
    query = f'"{team_name}" fútbol OR soccer'
    params = urllib.parse.urlencode({
        "q": query,
        "hl": hl,
        "gl": gl,
        "ceid": ceid,
    })
    return f"{_GNEWS_RSS_BASE}?{params}"


def _parse_feed(xml_content: bytes) -> List[str]:
    """
    Parsea el XML del feed RSS y extrae los titulares limpios.
    Usa feedparser con el contenido ya descargado (evita peticiones adicionales).
    """
    try:
        import feedparser  # lazy import — solo cargamos si el servicio se usa
        feed = feedparser.parse(xml_content)
        headlines = []
        for entry in feed.entries[:_MAX_HEADLINES]:
            title = entry.get("title", "").strip()
            # Limpiar sufijo "- Fuente" que agrega Google News
            title = re.sub(r"\s*-\s*[^-]{1,40}$", "", title).strip()
            if title and len(title) > 10:
                headlines.append(title)
        return headlines
    except ImportError:
        logger.warning("feedparser no está instalado — sin noticias RSS")
        return []
    except Exception as exc:
        logger.warning(f"Error parseando feed RSS: {exc}")
        return []


async def _fetch_rss_raw(url: str) -> Optional[bytes]:
    """Descarga el contenido del feed RSS con timeout estricto."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; SportsAI/1.0; "
                    "+https://github.com/sports-ai)"
                )
            },
            timeout=_RSS_TIMEOUT_SECONDS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.TimeoutException:
        logger.warning(f"Timeout al obtener RSS: {url}")
        return None
    except httpx.HTTPStatusError as exc:
        logger.warning(f"HTTP {exc.response.status_code} al obtener RSS: {url}")
        return None
    except Exception as exc:
        logger.warning(f"Error obteniendo RSS: {exc}")
        return None


class NewsRSSService:
    """
    Servicio de noticias vía Google News RSS.

    - Sin API Key requerida.
    - Caché en Redis para evitar peticiones duplicadas.
    - Fallback silencioso: si falla, retorna lista vacía.
    """

    async def get_team_headlines(
        self,
        team_name: str,
        lang: str = "es",
    ) -> List[str]:
        """
        Retorna hasta `_MAX_HEADLINES` titulares recientes sobre el equipo.

        Args:
            team_name: Nombre del equipo (ej: "Barcelona", "Real Madrid")
            lang: Idioma del feed ("es", "en", "pt")

        Returns:
            Lista de strings con los titulares. Vacía si no hay noticias o error.
        """
        cache_key = f"news_rss:{lang}:{team_name.lower().replace(' ', '_')}"

        # Intentar desde caché Redis
        try:
            redis = await get_redis()
            cached = await redis.get(cache_key)
            if cached:
                import json
                headlines = json.loads(cached)
                logger.debug(f"✓ RSS caché hit para {team_name} ({len(headlines)} noticias)")
                return headlines
        except Exception as exc:
            logger.debug(f"Redis no disponible para RSS caché: {exc}")

        # Obtener desde Google News RSS
        url = _build_rss_url(team_name, lang)
        logger.info(f"📰 Obteniendo noticias RSS: {team_name}")

        xml_content = await _fetch_rss_raw(url)
        if not xml_content:
            return []

        headlines = _parse_feed(xml_content)
        logger.info(f"📰 {team_name}: {len(headlines)} titulares obtenidos")

        # Guardar en caché Redis
        if headlines:
            try:
                redis = await get_redis()
                import json
                await redis.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(headlines))
            except Exception as exc:
                logger.debug(f"No se pudo guardar RSS en caché: {exc}")

        return headlines

    async def get_match_headlines(
        self,
        home_team: str,
        away_team: str,
        lang: str = "es",
    ) -> dict:
        """
        Obtiene noticias de ambos equipos en paralelo.

        Returns:
            {"home": [...titulares...], "away": [...titulares...]}
        """
        home_headlines, away_headlines = await asyncio.gather(
            self.get_team_headlines(home_team, lang),
            self.get_team_headlines(away_team, lang),
            return_exceptions=True,
        )

        return {
            "home": home_headlines if isinstance(home_headlines, list) else [],
            "away": away_headlines if isinstance(away_headlines, list) else [],
        }
