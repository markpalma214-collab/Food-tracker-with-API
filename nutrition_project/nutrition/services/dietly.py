"""
Thin wrapper around the Dietly food-search API.

Used by both the `import_food` management command and the `food_create`
view, so the request/error-handling logic lives in exactly one place.
"""
import os

import requests

API_URL = "https://api.getdietly.com/search"


class DietlyAPIError(Exception):
    """Raised when the Dietly API can't be reached or returns bad data."""


class DietlyNotConfigured(DietlyAPIError):
    """Raised when DIETLY_API_KEY isn't set."""


def search_food(query, limit=5):
    """
    Query Dietly for `query` and return the raw list[dict] of results.
    Raises DietlyNotConfigured / DietlyAPIError on failure — never returns
    None, so callers can rely on either getting a list or an exception.
    """
    api_key = os.environ.get('DIETLY_API_KEY')
    if not api_key:
        raise DietlyNotConfigured("DIETLY_API_KEY is not set.")

    try:
        response = requests.get(
            API_URL,
            params={'q': query, 'limit': limit},
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DietlyAPIError(f"Could not reach the food API: {exc}") from exc

    try:
        foods = response.json()
    except ValueError as exc:
        raise DietlyAPIError("Dietly API returned an unreadable response.") from exc

    if not isinstance(foods, list):
        raise DietlyAPIError("Dietly API returned an unexpected response format.")

    return foods


def get_first_match(query, limit=5):
    """
    Convenience helper for the common case: return the first matching food
    dict, or None if there were no results. Kept separate from search_food
    so it's easy to later add a food-selection step using the full list.
    """
    foods = search_food(query, limit=limit)
    return foods[0] if foods else None
