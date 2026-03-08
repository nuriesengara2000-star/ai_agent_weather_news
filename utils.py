"""
utils.py — Shared helpers for HTTP requests, formatting, and error handling.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10  # seconds


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ApiError(Exception):
    """Raised when an external API call fails."""


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def safe_get(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    allow_http_errors: bool = False,
) -> dict[str, Any]:
    """Perform a GET request and return parsed JSON.

    Args:
        url: The endpoint URL.
        params: Optional query parameters.
        timeout: Request timeout in seconds.
        allow_http_errors: If True, return the JSON body even on 4xx/5xx
            status codes instead of raising. Useful when the API encodes
            error details in the response body (e.g. OpenWeatherMap 404).

    Raises:
        ApiError: On network failures, timeouts, or unexpected HTTP errors.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)

        # Some APIs (like OpenWeatherMap) return useful JSON even on 404.
        # Let the caller handle those by setting allow_http_errors=True.
        if not allow_http_errors:
            response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        raise ApiError(
            "The service took too long to respond. Please try again later."
        )
    except requests.exceptions.ConnectionError:
        raise ApiError(
            "Could not connect to the service. Please check your network."
        )
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        raise ApiError(f"API returned HTTP {status}. The service may be down.")
    except requests.exceptions.RequestException as exc:
        logger.exception("Unexpected request error")
        raise ApiError(f"Request failed: {exc}")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_numbered_list(items: list[str]) -> str:
    """Format a list of strings as a numbered list."""
    if not items:
        return "No items to display."
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def truncate(text: str, max_length: int = 200) -> str:
    """Shorten text to max_length, adding '…' if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"
