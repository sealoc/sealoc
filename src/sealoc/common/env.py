"""Module for environment variables."""

import os

import dotenv

from pathlib import Path


# Set default env file path to .env file in project root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE: Path = PROJECT_ROOT / ".env"


# Load once
dotenv.load_dotenv(DEFAULT_ENV_FILE)


def get_default_path() -> Path:
    """
    Return the default .env file path.

    Returns
    -------
    Path to the default .env file at the project root.
    """
    return DEFAULT_ENV_FILE


def get_str(key: str, default: str | None = None) -> str | None:
    """
    Return an environment variable as a string, or a default.

    Arguments
    ---------
    key: Environment variable name.
    default: Value to return if the variable is not set.

    Returns
    -------
    Variable value as a string, or default if not set.
    """
    value = os.getenv(key, default)
    return value


def get_int(key: str, default: int | None = None) -> int | None:
    """
    Return an environment variable as an int, or a default.

    Arguments
    ---------
    key: Environment variable name.
    default: Value to return if the variable is not set.

    Returns
    -------
    Variable value as an int, or default if not set.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid int for env var {key}: {value}")


def get_bool(key: str, default: bool | None = None) -> bool | None:
    """
    Return an environment variable as a bool, or a default.

    Arguments
    ---------
    key: Environment variable name.
    default: Value to return if the variable is not set.

    Returns
    -------
    Variable value as a bool, or default if not set.
    """
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def require(key: str) -> str:
    """
    Return a required environment variable or raise an error.

    Arguments
    ---------
    key: Environment variable name.

    Returns
    -------
    Variable value as a string.
    """
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value
