"""Official Python SDK for the Finget passwordless login and notification API."""

from .client import VERSION, DEFAULT_AUTH_URL, DEFAULT_BASE_URL, Client
from .errors import ApiError, FingetError

__all__ = [
    "Client",
    "VERSION",
    "DEFAULT_BASE_URL",
    "DEFAULT_AUTH_URL",
    "FingetError",
    "ApiError",
]

__version__ = VERSION
