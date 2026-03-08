"""
tools.py — LangChain tool wrappers for external APIs.

Each tool validates input, calls the API, parses structured data,
and returns a formatted string for the agent to include in its answer.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool

from utils import safe_get, format_numbered_list, truncate, ApiError

# ── Default configuration ────────────────────────────────────────────────
# News language can be changed here or overridden via environment variable.
NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "en")


# ═════════════════════════════════════════════════════════════════════════
# 1. WEATHER  —  OpenWeatherMap
# ═════════════════════════════════════════════════════════════════════════

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. "London", "Tokyo", "New York".
    """
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Weather service is not configured (missing WEATHER_API_KEY)."

    city = city.strip()
    if not city:
        return "Please provide a city name."

    # OpenWeatherMap returns JSON with error details on 404, so we
    # allow HTTP errors and inspect the response body ourselves.
    try:
        data = safe_get(
            WEATHER_URL,
            params={"q": city, "appid": api_key, "units": "metric"},
            allow_http_errors=True,
        )
    except ApiError as exc:
        return f"Could not fetch weather data: {exc}"

    # --- Handle city not found (HTTP 404) ---
    cod = data.get("cod")
    if cod in (404, "404"):
        return (
            f"City '{city}' not found. "
            "Please check the spelling and try again."
        )
    if cod not in (200, "200"):
        msg = data.get("message", "Unknown error")
        return f"Weather lookup failed: {msg}"

    # --- Parse the structured response into a dict first ---
    weather_info = {
        "city": data.get("name", city),
        "country": data.get("sys", {}).get("country", ""),
        "description": (
            data.get("weather", [{}])[0]
            .get("description", "N/A")
            .capitalize()
        ),
        "temp": data.get("main", {}).get("temp", "N/A"),
        "feels_like": data.get("main", {}).get("feels_like", "N/A"),
        "humidity": data.get("main", {}).get("humidity", "N/A"),
        "wind_speed": data.get("wind", {}).get("speed", "N/A"),
    }

    # --- Format output ---
    location = weather_info["city"]
    if weather_info["country"]:
        location += f", {weather_info['country']}"

    return (
        f"Weather in {location}:\n"
        f"  Conditions : {weather_info['description']}\n"
        f"  Temperature: {weather_info['temp']}°C "
        f"(feels like {weather_info['feels_like']}°C)\n"
        f"  Humidity   : {weather_info['humidity']}%\n"
        f"  Wind       : {weather_info['wind_speed']} m/s"
    )


# ═════════════════════════════════════════════════════════════════════════
# 2. NEWS  —  NewsAPI
# ═════════════════════════════════════════════════════════════════════════

NEWS_URL = "https://newsapi.org/v2/everything"


@tool
def get_news(topic: str) -> str:
    """Search for the latest news articles about a topic.

    Args:
        topic: Subject to search, e.g. "artificial intelligence", "Japan".
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "News service is not configured (missing NEWS_API_KEY)."

    topic = topic.strip()
    if not topic:
        return "Please provide a topic to search for."

    try:
        data = safe_get(
            NEWS_URL,
            params={
                "q": topic,
                "apiKey": api_key,
                "pageSize": 5,
                "sortBy": "publishedAt",
                "language": NEWS_LANGUAGE,
            },
        )
    except ApiError as exc:
        return f"Could not fetch news: {exc}"

    # Check API-level error
    if data.get("status") != "ok":
        msg = data.get("message", "Unknown error from news API.")
        return f"News lookup failed: {msg}"

    articles = data.get("articles", [])
    if not articles:
        return f"No recent news articles found for '{topic}'."

    # Parse into structured list, then format
    headlines: list[str] = []
    for article in articles:
        title = article.get("title") or "Untitled"
        source = article.get("source", {}).get("name", "Unknown")
        desc = truncate(article.get("description") or "", max_length=120)
        headlines.append(f"{title} ({source}) — {desc}")

    return f"Latest news about '{topic}':\n" + format_numbered_list(headlines)


# ═════════════════════════════════════════════════════════════════════════
# 3. CURRENCY  —  ExchangeRate-API  [BONUS TOOL]
# ═════════════════════════════════════════════════════════════════════════

EXCHANGE_URL = "https://v6.exchangerate-api.com/v6"


@tool
def get_currency_rate(currency_pair: str) -> str:
    """Get the live exchange rate between two currencies (bonus tool).

    Args:
        currency_pair: Two ISO currency codes, e.g. "USD to EUR", "GBP/JPY".
    """
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    if not api_key:
        return (
            "Currency service is not configured (missing EXCHANGE_RATE_API_KEY). "
            "This is an optional bonus tool."
        )

    base, target = _parse_currency_pair(currency_pair)
    if not base or not target:
        return (
            "Could not parse the currency pair. "
            "Use a format like 'USD to EUR' or 'GBP/JPY'."
        )

    try:
        data = safe_get(f"{EXCHANGE_URL}/{api_key}/latest/{base}")
    except ApiError as exc:
        return f"Could not fetch exchange rate: {exc}"

    if data.get("result") != "success":
        error = data.get("error-type", "unknown error")
        return f"Exchange rate lookup failed: {error}"

    rate = data.get("conversion_rates", {}).get(target)
    if rate is None:
        return (
            f"Currency code '{target}' not found. "
            "Use a valid ISO 4217 code (e.g. USD, EUR, GBP)."
        )

    return f"Exchange rate: 1 {base} = {rate} {target}"


def _parse_currency_pair(text: str) -> tuple[str | None, str | None]:
    """Extract base and target codes from formats like 'USD TO EUR', 'USD/EUR'."""
    text = text.strip().upper().replace(",", "")

    for sep in (" TO ", "/", " "):
        if sep in text:
            parts = [p.strip() for p in text.split(sep, maxsplit=1)]
            if len(parts) == 2 and len(parts[0]) == 3 and len(parts[1]) == 3:
                return parts[0], parts[1]

    # Fallback: "USDEUR"
    if len(text) == 6 and text.isalpha():
        return text[:3], text[3:]

    return None, None


# ═════════════════════════════════════════════════════════════════════════
# Tool registry — imported by agent.py
# ═════════════════════════════════════════════════════════════════════════

ALL_TOOLS = [get_weather, get_news, get_currency_rate]
